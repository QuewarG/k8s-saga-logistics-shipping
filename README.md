# Laboratorio: Patrón SAGA para Logística y Envío con Kubernetes

Este repositorio contiene la implementación de un flujo de logística y envío de productos utilizando una arquitectura de microservicios. El proyecto demuestra el **patrón de orquestación SAGA** para gestionar transacciones distribuidas, asegurando la atomicidad de la operación completa.

En caso de que un paso falle, el orquestador iniciará una serie de **transacciones de compensación** para revertir las acciones ya completadas, garantizando así la integridad de los datos y manteniendo un bajo acoplamiento entre servicios.

## Arquitectura de Microservicios

El flujo completo se compone de 10 microservicios coordinados por un **Orquestador**. Tu misión es elegir uno de los microservicios de la tabla, implementarlo y desplegarlo en Kubernetes.

| #      | Microservicio           | Puerto   | Falla Aleatoria | Acción Principal                                        | Compensación                                                |
| ------ | ----------------------- | -------- | --------------- | ------------------------------------------------------- | ----------------------------------------------------------- |
| **1**  | Orchestrator            | 5000     | No              | Coordina todas las operaciones                          | Coordina compensaciones                                     |
| **2**  | Warehouse Service       | 5001     | No              | Reserva espacio en almacén                              | Liberar espacio reservado                                   |
| **3**  | Inventory Service       | 5002     | ⚠️ 30%          | Descontar inventario                                    | Restock de productos                                        |
| **4**  | Package Service         | 5003     | No              | Empaquetar productos                                    | Deshacer empaquetado                                        |
| **5**  | Label Service           | 5004     | ⚠️ 20%          | Generar etiqueta de envío                               | Anular etiqueta                                             |
| **6**  | Carrier Service         | 5005     | No              | Asignar transportista                                   | Cancelar asignación                                         |
| **7**  | Pickup Service          | 5006     | No              | Programar recolección                                   | Cancelar recolección                                        |
| **8**  | Payment Service         | 5007     | ⚠️ 15%          | Procesar pago                                           | Reembolso/reversa de cargo                                  |
| **9**  | Notification Service    | 5008     | No              | Notificar confirmación al cliente                       | Notificar cancelación                                       |
| **10** | Tracking Service        | 5009     | No              | Actualizar estado a “EN TRÁNSITO”                       | Actualizar a “CANCELADO”                                    |
| **11** | Customer Service | 5010 | No              | Actualizar el historial del cliente (pedido completado) | Revertir estado del pedido (pedido cancelado) |

### Lógica de Compensación y Notificación

Si uno de los servicios propensos a fallar (Inventory, Label, Payment) devuelve un error, el Orquestador detendrá el flujo principal e iniciará la cadena de compensaciones.

Al final, ya sea por éxito o por fallo, los últimos tres servicios **siempre se ejecutarán** para registrar el estado final del pedido:
*   **En caso de éxito:** Notifican "pedido confirmado", marcan "EN TRÁNSITO", etc.
*   **En caso de fallo:** Notifican "pedido cancelado", marcan "CANCELADO", etc.

Al implementar estos tres servicios, ten en cuenta que su lógica de "compensación" es simplemente registrar el estado de cancelación, no necesariamente deshacer una acción previa.

## Guía de Implementación

Cada microservicio puede ser desarrollado en el lenguaje que prefieras. Lo esencial es que siga estas directrices para integrarse correctamente en el clúster de Kubernetes.

#### 1. Endpoints Requeridos
Tu servicio debe exponer, como mínimo:
*   Un endpoint para la **acción principal** (ej. `POST /reserve`).
*   Un endpoint para la **acción de compensación** (ej. `POST /cancel_reservation`).
*   Un endpoint para revisar los elementos en la memoria del microservicio (ej. `POST /reservas`).
*   Un endpoint de `livenessProbe` para chequeo de salud (ej. `GET /health`) que devuelva un código `HTTP 200 OK`.

#### 2. Variables de Entorno
La aplicación debe ser configurable mediante variables de entorno, principalmente `SERVICE_NAME` y `SERVICE_PORT`. Esto permite que el mismo contenedor se comporte de manera diferente según cómo se despliegue.

#### 3. Empaquetado con Docker
Crea un `Dockerfile` para tu servicio. Este archivo se encargará de construir una imagen portable con todo lo necesario para ejecutar tu aplicación.

#### 4. Manifiestos de Kubernetes
Cada servicio requiere dos archivos YAML:
*   `deployment.yaml`: Define cómo Kubernetes debe ejecutar los contenedores de tu aplicación (réplicas, imagen, puertos, variables de entorno, etc.).
*   `service.yaml`: Crea un punto de acceso de red estable (un nombre DNS interno y una IP) para tus pods. Esto permite que el Orquestador se comunique con tu servicio sin necesidad de conocer la IP de cada pod.

A continuación, se presentan los manifiestos de `warehouse-service` como plantilla. **Recuerda adaptar los nombres, puertos e imagen a tu propio servicio.**

### Plantilla: `deployment.yaml`

```yaml
# services/warehouse-service/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: warehouse-service # <-- CAMBIAR POR TU SERVICIO
  namespace: saga-shipping
  labels:
    app: warehouse-service # <-- CAMBIAR
spec:
  replicas: 1 # Puedes empezar con 1
  selector:
    matchLabels:
      app: warehouse-service # <-- CAMBIAR
  template:
    metadata:
      labels:
        app: warehouse-service # <-- CAMBIAR
    spec:
      containers:
      - name: warehouse-service-container # <-- CAMBIAR
        image: warehouse-service:latest # <-- CAMBIAR (usa tu imagen)
        imagePullPolicy: IfNotPresent # Ideal para desarrollo con Minikube
        ports:
        - containerPort: 5001 # <-- CAMBIAR
          name: http
        env:
        - name: SERVICE_NAME
          value: "warehouse-service" # <-- CAMBIAR
        - name: SERVICE_PORT
          value: "5001" # <-- CAMBIAR
        # Opcional: Para servicios que simulan fallos
        # - name: FAILURE_RATE
        #   value: "0.3" 
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health # Endpoint de chequeo
            port: 5001 # <-- CAMBIAR
          initialDelaySeconds: 15
          periodSeconds: 20
```

### Plantilla: `service.yaml`

```yaml
# services/warehouse-service/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: warehouse-service # <-- CAMBIAR
  namespace: saga-shipping
  labels:
    app: warehouse-service # <-- CAMBIAR
spec:
  type: ClusterIP # Solo accesible dentro del clúster
  selector:
    app: warehouse-service # <-- CAMBIAR
  ports:
  - name: http
    protocol: TCP
    port: 5001        # Puerto por el que el Service escucha
    targetPort: 5001  # Puerto del contenedor al que se redirige el tráfico
```

## Flujo de Trabajo y Comandos

Sigue estos pasos para desplegar tu microservicio en el clúster local de Minikube.

#### Paso 1: Levantar el Entorno Base
El `namespace` aísla nuestros servicios del resto del clúster. Aplícalo una sola vez.
```bash
kubectl apply -f k8s/namespace.yaml
```

#### Paso 2: Construir la Imagen Docker
Desde el directorio de tu servicio (donde está el `Dockerfile`), ejecuta:
```bash
# Ejemplo para warehouse-service
docker build -t warehouse-service:latest .
```

#### Paso 3: Cargar la Imagen en Minikube
Para que Minikube pueda usar la imagen que acabas de construir localmente sin necesidad de un registro externo, usa el siguiente comando:
```bash
# Ejemplo para warehouse-service
minikube image load warehouse-service:latest
```

#### Paso 4: Desplegar el Servicio en Kubernetes
Aplica tus archivos de manifiesto para crear el `Deployment` y el `Service`.
```bash
# Ejemplo para warehouse-service
kubectl apply -f services/warehouse-service/k8s/deployment.yaml
kubectl apply -f services/warehouse-service/k8s/service.yaml
```

## Comandos Útiles para Gestión

#### Listar Pods
Para ver si tus contenedores están corriendo correctamente.
```bash
kubectl get pods -n saga-shipping
```

#### Port-Forwarding (para pruebas)
Para acceder a tu servicio desde tu máquina local como si estuviera corriendo allí.
```bash
# Conecta tu puerto local 8080 al puerto 5001 del servicio warehouse-service
kubectl port-forward svc/warehouse-service 8080:5001 -n saga-shipping
```
Ahora puedes hacer peticiones a `http://localhost:8080`.

#### Reiniciar un Deployment
Útil si necesitas forzar que los pods se recreen con la imagen más reciente (si usas la tag `:latest`) o para recargar alguna configuración.
```bash
kubectl rollout restart deployment/warehouse-service -n saga-shipping
```

#### Eliminar el Entorno Completo
Para limpiar todos los recursos creados en este laboratorio.
```bash
kubectl delete namespace saga-shipping
```