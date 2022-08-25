from rest_framework.response import Response
from rest_framework import viewsets, views, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from reportcreator_api.users.models import PentestUser
from reportcreator_api.users.permissions import IsSelfOrAdminOrReadOnly
from reportcreator_api.users.serializers import PentestUserSerializer


class PentestUserViewSet(viewsets.ModelViewSet):
    queryset = PentestUser.objects.filter(is_active=True)
    serializer_class = PentestUserSerializer
    permission_classes = [IsSelfOrAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']

    @action(detail=False, methods=['get'])
    def self(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class TokenLogoutView(views.APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

