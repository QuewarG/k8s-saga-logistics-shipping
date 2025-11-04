from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Warehouse Service")

# Variables de entorno
SERVICE_NAME = os.getenv("SERVICE_NAME", "warehouse-service")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "5001"))

# Almacenamiento local en memoria
reservas = []

@app.post("/reserve")
async def reserve_space(request: Request):
    """Reserva espacio en el almacén para un producto asociado a un usuario."""
    data = await request.json()
    user = data.get("user")
    product = data.get("product")

    if not user or not product:
        return JSONResponse({"error": "Faltan campos requeridos: user, product"}, status_code=400)

    reserva = {"user": user, "product": product}
    reservas.append(reserva)

    return JSONResponse({
        "message": f"Espacio reservado en almacén para {user} - producto: {product}",
        "service": SERVICE_NAME
    }, status_code=200)

@app.post("/cancel")
async def cancel_reservation(request: Request):
    """Cancela (compensación) una reserva previamente hecha."""
    data = await request.json()
    user = data.get("user")
    product = data.get("product")

    if not user or not product:
        return JSONResponse({"error": "Faltan campos requeridos: user, product"}, status_code=400)

    # Buscar y eliminar la reserva
    for r in reservas:
        if r["user"] == user and r["product"] == product:
            reservas.remove(r)
            return JSONResponse({
                "message": f"Reserva cancelada para {user} - producto: {product}",
                "service": SERVICE_NAME
            }, status_code=200)

    return JSONResponse({
        "message": f"No se encontró reserva para {user} - producto: {product}",
        "service": SERVICE_NAME
    }, status_code=404)

@app.get("/reservas")
async def list_reservations():
    """Devuelve todas las reservas actuales."""
    return JSONResponse({"reservas": reservas, "count": len(reservas)})

@app.get("/health")
async def health_check():
    """Verifica el estado del servicio."""
    return JSONResponse({
        "service": SERVICE_NAME,
        "status": "healthy"
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
