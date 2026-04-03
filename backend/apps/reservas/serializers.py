import datetime

from rest_framework import serializers

from apps.common.utils import nombre_usuario
from .models import EstadoReserva, OrigenReserva, Reserva
from .validators import validar_horario_reserva


class ReservaPublicaSerializer(serializers.ModelSerializer):
    """
    Para el formulario web: solo campos que el cliente puede enviar.
    No expone datos internos ni permite asignar mesa o estado.
    """

    class Meta:
        model = Reserva
        fields = (
            "id",
            "nombre_contacto",
            "telefono_contacto",
            "email_contacto",
            "fecha",
            "hora",
            "cantidad_personas",
            "observaciones",
        )

    def validate(self, attrs):
        fecha = attrs.get("fecha")
        hora = attrs.get("hora")

        if fecha and fecha < datetime.date.today():
            raise serializers.ValidationError(
                {"fecha": "No se pueden hacer reservas en fechas pasadas."}
            )

        if fecha and hora:
            validar_horario_reserva(fecha, hora)

        return attrs

    def create(self, validated_data):
        return Reserva.objects.create(
            **validated_data,
            origen=OrigenReserva.WEB,
            estado=EstadoReserva.PENDIENTE,
        )


class ReservaInternaSerializer(serializers.ModelSerializer):
    """Para el panel interno: campos completos."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    origen_display = serializers.CharField(source="get_origen_display", read_only=True)
    mesa_etiqueta = serializers.SerializerMethodField()
    gestionada_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = (
            "id",
            "usuario",
            "nombre_contacto",
            "telefono_contacto",
            "email_contacto",
            "fecha",
            "hora",
            "cantidad_personas",
            "mesa",
            "mesa_etiqueta",
            "estado",
            "estado_display",
            "origen",
            "origen_display",
            "observaciones",
            "gestionada_por",
            "gestionada_por_nombre",
            "creado_en",
            "actualizado_en",
        )
        read_only_fields = ("gestionada_por", "creado_en", "actualizado_en")

    def get_mesa_etiqueta(self, obj):
        return obj.mesa.etiqueta if obj.mesa else ""

    def get_gestionada_por_nombre(self, obj):
        return nombre_usuario(obj.gestionada_por)

    def validate(self, attrs):
        fecha = attrs.get("fecha", getattr(self.instance, "fecha", None))
        hora = attrs.get("hora", getattr(self.instance, "hora", None))
        if fecha and hora:
            validar_horario_reserva(fecha, hora)
        return attrs


class CambiarEstadoReservaSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoReserva.choices)
    observaciones = serializers.CharField(required=False, allow_blank=True)
