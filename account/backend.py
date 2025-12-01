from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated  # Korunan endpoint için
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# -------------------
# JWT Login Endpoint (DRF Simple JWT kullanır)
# -------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Token içine ekstra bilgiler ekleyelim
        token['username'] = user.username
        token['is_staff'] = user.is_staff          # Admin mi?
        token['is_operator'] = getattr(user, 'is_operator', False)  # Operator bilgisi
        # Eğer User modelinde is_operator alanı yoksa False döner

        return token

# -------------------
# Custom Token View
# -------------------
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
# -------------------
# GET: Hizmetler
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_services(request):
    data = ["Hizmet A", "Hizmet B", "Hizmet C"]  # TODO: DB'den çekilecek
    return Response(data)

# -------------------
# POST: Hizmet ekleme (Admin)
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_services(request):
    if not request.user.is_staff:  # Admin kontrolü
        return Response({"error": "Yetkisiz erişim"}, status=status.HTTP_403_FORBIDDEN)
    data = ["5 yıldız bla bla"]  # TODO: DB'ye kaydetme
    return Response(data)

# -------------------
# GET: Ustalar
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_operators(request):
    data = ["Usta A", "Usta B", "Usta C"]  # TODO: DB'den çekilecek
    return Response(data)

# -------------------
# GET: Usta bilgisi
# -------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_operator_info(request):
    data = ["5 yıldız bla bla"]  # TODO: DB'den çekilecek
    return Response(data)

# -------------------
# POST: Usta bilgisi ekleme (Admin)
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_operator_info(request):
    if not request.user.is_staff:  # Admin kontrolü
        return Response({"error": "Yetkisiz erişim"}, status=status.HTTP_403_FORBIDDEN)
    data = ["5 yıldız bla bla"]  # TODO: DB'ye kaydet
    return Response(data)

# -------------------
# POST: Seçilen usta
# -------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_operator(request):
    selected = request.data.get('selected')
    if not selected:
        return Response(
            {"error": "Seçilen ustayı belirtmelisiniz."},
            status=status.HTTP_400_BAD_REQUEST
        )
    # TODO: DB'ye kaydet -> Hizmet/Usta/İşlem
    response = {"message": f"{selected} seçildi"}
    return Response(response)
