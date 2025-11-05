# 🚚 Transport Service

El **Transport Service** es un microservicio dentro del sistema logístico **Saga Logistics** encargado de **gestionar la asignación y cancelación de transportistas** para los pedidos.  
Fue desarrollado en **Python (Flask)**, ejecutado en **Docker** y diseñado para integrarse con otros servicios a través de APIs REST.

---

## 🧩 ¿Cómo funciona?

El servicio se encarga de:
1. **Asignar automáticamente** un transportista disponible (simulado aleatoriamente) a un pedido cuando se recibe una solicitud desde el orquestador o cliente externo.
2. **Cancelar una asignación existente** si ocurre un error o se revierte una operación (por ejemplo, en una transacción SAGA).
3. **Mantener un registro temporal en memoria** con las asignaciones activas.
4. Proveer un **endpoint de salud (`/health`)** usado por Kubernetes para verificar el estado del servicio.

En un entorno distribuido, este servicio es parte del flujo de **coordinación SAGA**, donde colabora con otros servicios como:
- **Order Service** 🧾 (crea pedidos)
- **Label Service** 🏷️ (genera etiquetas)
- **Transport Service** 🚚 (asigna transportistas)
  
Cada uno expone endpoints que el orquestador usa para ejecutar y compensar pasos de una transacción distribuida.

---

## 📦 Endpoints

### 🔹 `GET /health`
Verifica que el servicio esté activo.

**Ejemplo:**
```bash
curl http://localhost:5005/health
Respuesta:

json
Copiar código
{"service": "transport-service", "status": "ok"}
🔹 POST /assign_carrier
Asigna un transportista aleatorio a un pedido.

Ejemplo:

bash
Copiar código
curl -X POST http://localhost:5005/assign_carrier \
  -H "Content-Type: application/json" \
  -d '{"orderId": "ORD-1001"}'
Respuesta:

json
Copiar código
{"carrier": {"carrierId": "CRR-62-FastShip", "assigned": true}}
🔹 POST /cancel_assignment
Cancela una asignación existente para un pedido.

Ejemplo:

bash
Copiar código
curl -X POST http://localhost:5005/cancel_assignment \
  -H "Content-Type: application/json" \
  -d '{"orderId": "ORD-1001"}'
Respuesta:

json
Copiar código
{"status": "cancelled", "carrierId": "CRR-62-FastShip", "orderId": "ORD-1001"}
🔹 GET /assignments
Lista todas las asignaciones activas almacenadas en memoria.

Ejemplo:

bash
Copiar código
curl http://localhost:5005/assignments
Respuesta:

json
Copiar código
{"ORD-1001": {"carrier": {"assigned": true, "carrierId": "CRR-62-FastShip"}}}
⚙️ Ejecución local con Docker
1️⃣ Construir la imagen
bash
Copiar código
docker build -t transport-service .
2️⃣ Ejecutar el contenedor
bash
Copiar código
docker run -d -p 5005:5005 transport-service
3️⃣ Verificar el estado
bash
Copiar código
curl http://localhost:5005/health
☸️ Despliegue en Kubernetes (K8s)
El servicio puede desplegarse fácilmente en Kubernetes.
Asegúrate de que la imagen esté disponible para el cluster (por ejemplo, usando minikube image load o subiéndola a Docker Hub).

Ejemplo de Deployment y Service:

bash
Copiar código
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
Verificar el estado:

bash
Copiar código
kubectl get pods -n saga-shipping
kubectl port-forward svc/transport-service 5005:5005 -n saga-shipping
Luego, puedes probarlo:

bash
Copiar código
curl http://localhost:5005/health
🧰 Variables de entorno
Variable	Descripción	Valor por defecto
SERVICE_NAME	Nombre del servicio	transport-service
SERVICE_PORT	Puerto interno del contenedor	5005

🧱 Estructura del proyecto
css
Copiar código
services/
└── transport-service/
    ├── app/
    │   ├── main.py
    │   └── requirements.txt
    ├── Dockerfile
    ├── k8s/
    │   ├── deployment.yaml
    │   └── service.yaml
    └── README.md
🧑‍💻 Desarrollado con
🐍 Python 3.11
🌶️ Flask
🐳 Docker
☸️ Kubernetes
Autor
Desarrollado por Johan Acosta
Rama: jsar
Parte del proyecto Saga Logistics - K8s SAGA Implementation