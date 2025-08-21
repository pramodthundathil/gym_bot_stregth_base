
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from Index import urls
import Index
import Members
from Members import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path("",include("Index.urls")),
    path("members/",include('Members.urls')),
    path("finance/",include('Finance.urls')),
    path("enquiries/",include('enquiry.urls')),
    path("foodlog/",include("foodlog.urls"))
]
urlpatterns = urlpatterns+static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
