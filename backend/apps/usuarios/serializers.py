from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario


class TokenPersonalizadoSerializer(TokenObtainPairSerializer):
    """
    Extiende el token JWT estándar para incluir datos útiles del usuario
    directamente en el payload, evitando un request extra al perfil.
    También bloquea el login si el usuario está inactivo.
    """

    def validate(self, attrs):
        datos = super().validate(attrs)
        usuario = self.user

        if not usuario.activo:
            raise serializers.ValidationError(
                {"detalle": "Esta cuenta está desactivada. Contactá a tu supervisor."}
            )

        datos["usuario"] = {
            "id": usuario.id,
            "username": usuario.username,
            "nombre": usuario.get_full_name(),
            "rol": usuario.rol,
            "primer_ingreso": usuario.primer_ingreso,
        }
        return datos


class PerfilSerializer(serializers.ModelSerializer):
    """Serializer de lectura/actualización del perfil propio."""

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "activo",
            "primer_ingreso",
            "avatar",
            "creado_en",
        )
        read_only_fields = (
            "id",
            "username",
            "rol",
            "activo",
            "primer_ingreso",
            "creado_en",
        )


class CambiarContrasenaSerializer(serializers.Serializer):
    """Permite al usuario cambiar su propia contraseña."""

    contrasena_actual = serializers.CharField(write_only=True)
    contrasena_nueva = serializers.CharField(write_only=True, min_length=8)
    contrasena_nueva_confirmacion = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["contrasena_nueva"] != attrs["contrasena_nueva_confirmacion"]:
            raise serializers.ValidationError(
                {"contrasena_nueva_confirmacion": "Las contraseñas no coinciden."}
            )
        return attrs


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """Serializer para que administradores gestionen usuarios."""

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "telefono",
            "rol",
            "activo",
            "primer_ingreso",
            "creado_en",
        )
        read_only_fields = ("id", "primer_ingreso", "creado_en")

    def create(self, validated_data):
        # Al crear desde admin, la contraseña inicial es el username
        # y se marca primer_ingreso=True para forzar cambio
        contrasena = validated_data.pop("password", validated_data["username"])
        usuario = Usuario(**validated_data)
        usuario.set_password(contrasena)
        usuario.primer_ingreso = True
        usuario.save()
        return usuario
