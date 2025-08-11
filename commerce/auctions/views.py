from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import User
from .models import Listing
from .models import Bid
from .models import Comment
from .models import Watchlist

from decimal import Decimal

def index(request):
    listings_with_bids = []
    listings = Listing.objects.filter(is_active=True).order_by("-created_at")
    for listing in listings:
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
        listings_with_bids.append({
            "listing": listing,
            "highest_bid": highest_bid            
        })
    
    return render(request, "auctions/index.html", {
        "listings": listings,
        "listings_with_bids": listings_with_bids
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"] 
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
    

def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST["image_url"]
        category = request.POST["category"]
        
        # check if required fields are not empty


        if not all([title, description, starting_bid]):
            return render(request, "auctions/create.html", {
                "message": "Fill in all Required Fields"
            })
        try:
            starting_bid = float(starting_bid)
        except:
            return render(request, "auctions/create.html", {
                "message": "starting bid must be a number"
            })
        
        # create and save the listing

        listing = Listing(
            title=title,
            description=description,
            starting_bid=starting_bid,
            image_url=image_url if image_url else None,
            category=category if category else None,
            owner = request.user #logged in user
        )
        listing.save()

        return HttpResponseRedirect(reverse("index"))
    return render(request, "auctions/create.html")

def view_listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    highest_bid = Bid.objects.filter(listing=listing).order_by("-amount").first()
    comments = Comment.objects.filter(listing=listing)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "comment":
            placed_comment = request.POST.get("comment")

        # create and save comment
                
            if placed_comment:
                comment = Comment(
                user = request.user,
                listing = listing,
                text = placed_comment if placed_comment else None           
                )
                comment.save()
            
        elif action == "bid":
            if listing.owner == request.user:
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "bid": highest_bid,
                    "comments": comments,
                    "error": "You cannot bid on your own listing"
                })
            else:
                bid_input = request.POST.get("bid")
                if not bid_input:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "bid": highest_bid,
                        "comments": comments
                        })
                try:
                    placed_bid = Decimal(bid_input)
                except:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "message": "Enter a valid bid amount",
                        "bid": highest_bid,
                        "comments": comments
                        })
                if highest_bid is None:
                    current_bid = listing.starting_bid
                else:
                    current_bid = highest_bid.amount
                if placed_bid < current_bid:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "error": "Place Bid Higher Than The Current Bid",
                        "bid" : highest_bid,
                        "comments": comments
                        })
                else:
                    bid = Bid(
                    user = request.user,
                    listing = listing,
                    amount = placed_bid
                    )
                    bid.save()
            
            # save ke baad highest bid update karo

                highest_bid = bid
        elif action == "watchlist":
            
            # watchlist
                _, created = Watchlist.objects.get_or_create(user = request.user, listing=listing)
                if created:
                    message = "Added to Watchlist"
                else:
                     message = "Already Added"
                return render(request, "auctions/listing.html", {
                    "listing": listing,
                    "bid" : highest_bid,
                    "comments": comments,
                    "message" : message
                    })
            # CLose Auction

        
        elif action == "closed_auction":
            listing = get_object_or_404(Listing, pk=listing_id)
            listing.is_closed = True
            
            highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
            if highest_bid:
                listing.winner = highest_bid.user

            listing.save()
            



    return render(request, "auctions/listing.html", { 
        "listing": listing,
        "bid": highest_bid,
        "comments": comments
    })    

@login_required
def watchlist_view(request):
    user_watchlist = Watchlist.objects.filter(user=request.user, listing__is_active = True)
    listings = [entry.listing for entry in user_watchlist]
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })
@login_required
def categories(request):
    if request.method == "GET":
        categories = Listing.objects.values_list('category', flat=True).distinct()
        if categories:
            return render(request, "auctions/categories.html", {
                "categories": categories
                })
        else:
            return render(request, "auctions/categories.html", {
                "message": "There are no categories."
            })
        
def categories_listing(request, category_name):
    listings = Listing.objects.filter(category=category_name, is_active=True)
    context = {
        "category": category_name,
        "listings": listings
    }
    if not listings.exists():
        context["message"]= "There are no listings available in this category now."

    return render(request, "auctions/category_listing.html", context)
        