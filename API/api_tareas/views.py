from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import ProductosSerializer
from .authentication import FirebaseAuthentication
from backend.firebase_config import get_firestore_client
from firebase_admin import firestore

db = get_firestore_client()


class ProductoAPIView(APIView):

    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, producto_id=None):
        uid_usuario = request.user.uid
        rol_usuario = request.user.rol

        limit = int(request.query_params.get('limit', 10))
        tipo = request.query_params.get('tipo')  # 🔥 clave

        # =========================
        # 🔥 ADMIN
        # =========================
        if rol_usuario == 'administrador':

            if tipo == "solicitudes":
                mensaje = "Todas las solicitudes"

                solicitudes_ref = db.collection('api_solicitudes').stream()

                data = [
                    {**doc.to_dict(), "id": doc.id, "tipo": "solicitud"}
                    for doc in solicitudes_ref
                ]

            else:
                mensaje = "Todos los productos"

                productos_ref = db.collection('api_productos').stream()

                data = [
                    {**doc.to_dict(), "id": doc.id, "tipo": "producto"}
                    for doc in productos_ref
                ]

        # =========================
        # 🔥 USUARIO NORMAL
        # =========================
        else:

            if tipo == "solicitudes":
                mensaje = "Mis solicitudes"

                solicitudes_ref = db.collection('api_solicitudes') \
                    .where('usuario_id', '==', uid_usuario) \
                    .stream()

                data = [
                    {**doc.to_dict(), "id": doc.id, "tipo": "solicitud"}
                    for doc in solicitudes_ref
                ]

            else:
                mensaje = "Listado de productos"

                productos_ref = db.collection('api_productos').stream()

                data = [
                    {**doc.to_dict(), "id": doc.id, "tipo": "producto"}
                    for doc in productos_ref
                ]

        # 🔥 Ordenar
        data = sorted(data, key=lambda x: x.get('fecha_creacion', ''), reverse=True)

        # 🔥 Limitar
        data = data[:limit]

        return Response({ "mensaje": mensaje, "Total en pagina": len(data), "datos": data, "next_page_token": data[-1]['id'] if data else None}, status=status.HTTP_200_OK)

    # ==================
    # POST - Crear
    # ==================
    def post(self, request):

        serializer = ProductosSerializer(data=request.data)
        rol_usuario = request.user.rol

        if serializer.is_valid():

            datos_validados = serializer.validated_data
            datos_validados['usuario_id'] = request.user.uid
            datos_validados['fecha_creacion'] = firestore.SERVER_TIMESTAMP

            try:
                # 👨‍💼 ADMIN → crea producto
                if rol_usuario == 'administrador':

                    nuevo_doc = db.collection('api_productos').add(datos_validados)
                    id_generado = nuevo_doc[1].id

                    return Response(
                        {
                            "mensaje": "producto creado correctamente",
                            "id": id_generado
                        },
                        status=status.HTTP_201_CREATED
                    )

                # 👤 USUARIO → crea solicitud
                else:
                    datos_validados['producto_id'] = request.data.get('producto_id')

                    nuevo_doc = db.collection('api_solicitudes').add(datos_validados)
                    id_generado = nuevo_doc[1].id

                    return Response(
                        {
                            "mensaje": "solicitud creada correctamente",
                            "id": id_generado
                        },
                        status=status.HTTP_201_CREATED
                    )

            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # =================
    # PUT - Actualizar
    # =================
    def put(self, request, producto_id=None):

        if not producto_id:
            return Response(
                {"error": "El ID es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto_ref = db.collection('api_productos').document(producto_id)
            doc = producto_ref.get()

            if not doc.exists:
                return Response(
                    {"error": "No encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            producto_data = doc.to_dict()

            # 🔥 CORRECCIÓN IMPORTANTE
            if producto_data.get('usuario_id') != request.user.uid or    request.user.rol != 'administrador':
                return Response(
                    {"error": "No tienes acceso a este producto"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = ProductosSerializer(
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                producto_ref.update(serializer.validated_data)

                return Response(
                    {
                        "mensaje": f"producto {producto_id} actualizado",
                        "datos": serializer.validated_data
                    },
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # ==================
    # DELETE - Eliminar
    # ==================
    def delete(self, request, producto_id=None):

        if not producto_id:
            return Response(
                {"error": "El ID es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto_ref = db.collection('api_productos').document(producto_id)
            doc = producto_ref.get()

            if not doc.exists:
                return Response(
                    {"error": "No encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            producto_data = doc.to_dict()

            # 🔥 CORRECCIÓN IMPORTANTE
            if producto_data.get("usuario_id") != request.user.uid or request.user.rol != 'administrador':
                return Response(
                    {"error": "No tienes permiso para eliminar este producto"},
                    status=status.HTTP_403_FORBIDDEN
                )

            producto_ref.delete()

            return Response(
                {"mensaje": f"producto {producto_id} eliminado"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )