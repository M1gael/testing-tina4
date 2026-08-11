from django.contrib.auth import get_user_model
from django.shortcuts import render
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from .models import Bookmark


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "title", "url"]


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def bookmarks_api(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        if not request.data.get("url"):
            return Response({"error": "url is required"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = BookmarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(BookmarkSerializer(Bookmark.objects.all(), many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    if request.data.get("username") != "demo" or request.data.get("password") != "demo":
        return Response({"error": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    user, _ = get_user_model().objects.get_or_create(username="demo")
    return Response({"token": str(AccessToken.for_user(user))})


def bookmarks_page(request):
    return render(request, "bookmarks.html", {"bookmarks": Bookmark.objects.all()})
