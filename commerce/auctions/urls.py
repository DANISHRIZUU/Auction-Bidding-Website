from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create"),
    path("listing/<int:listing_id>/", views.view_listing, name="listing"),
    path("watchlist/", views.watchlist_view, name="watchlist"),
    path("categories/", views.categories, name="categories"),
    path("category/<str:category_name>/", views.categories_listing, name="category_listings")
]
