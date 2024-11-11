# views.py

from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer
from .models import User, Event, Ticket, TicketPurchase
from .models import Event, TicketPurchase
from .serializers import EventSerializer, TicketPurchaseSerializer, TicketSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication


# Event Management Views

class CreateEventView(APIView):
    permission_classes = [IsAdminUser]  # Only Admin can create events

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EventCreateView(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAdminUser]

class EventListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

class TicketPurchaseView(generics.CreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    def create(self, request, *args, **kwargs):
        event = Event.objects.get(id=kwargs['event_id'])
        quantity = request.data.get('quantity')
        if event.tickets_sold + quantity > event.total_tickets:
            return Response({"error": "Not enough tickets available"}, status=status.HTTP_400_BAD_REQUEST)
        # Create ticket
        ticket = Ticket.objects.create(user=request.user, event=event, quantity=quantity)
        event.tickets_sold += quantity
        event.save()
        return Response(TicketSerializer(ticket).data, status=status.HTTP_201_CREATED)
    
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class FetchEventsView(APIView):
    permission_classes = [IsAuthenticated]  # Authenticated users can fetch events

    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


# Ticket Purchase View

class PurchaseTicketView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can purchase tickets

    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get quantity from request body
        quantity = request.data.get("quantity")
        if not quantity or quantity <= 0:
            return Response({"detail": "Quantity must be greater than 0."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a ticket purchase entry
        ticket_purchase = TicketPurchase.objects.create(
            user=request.user, event=event, quantity=quantity
        )
        serializer = TicketPurchaseSerializer(ticket_purchase)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
