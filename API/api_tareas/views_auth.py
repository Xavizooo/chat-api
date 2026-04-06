import os
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from firebase_admin import auth, firestore
from backend.firebase_config import get_firestore_client

# Inicializar Firestore correctamente
db = get_firestore_client()


class RegistroAPIView(APIView):
    """
    Endpoint público para registrar un nuevo usuario
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        rol = request.data.get('rol')

        if not email or not password or not rol:
            return Response(
                {"error": "Faltan credenciales"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Crear usuario en Firebase Authentication
            user = auth.create_user(
                email=email,
                password=password
            )

            # Guardar perfil en Firestore
            db.collection('perfiles').document(user.uid).set({
                'email': email,
                'rol': "aprendiz",
                'fecha_registro': firestore.SERVER_TIMESTAMP
            })

            return Response(
                {
                    "mensaje": "Usuario registrado exitosamente",
                    "uid": user.uid
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginAPIView(APIView):
    """
    Endpoint público que valida credenciales y devuelve el JWT de Firebase
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        api_key = os.getenv('FIREBASE_WEB_API_KEY')

        if not email or not password:
            return Response(
                {"error": "Faltan credenciales"},
                status=status.HTTP_400_BAD_REQUEST
            )


        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            firebase_response = requests.post(url, json=payload)
            data = firebase_response.json()

            if firebase_response.status_code == 200:
                return Response(
                    {
                        "mensaje": "Login exitoso",
                        "token": data.get("idToken"),
                        "uid": data.get("localId")
                    },
                    status=status.HTTP_200_OK
                )
            else:
                error_msg = data.get('error', {}).get('message', 'Error desconocido')
                return Response(
                    {"error": error_msg},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )