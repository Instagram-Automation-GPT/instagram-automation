from django.contrib import admin
from django.urls import path
from Data_Manager.serve import serve_minio_image, serve_minio_video
from Data_Manager.publish import publish_content, clients, queue_log,queue_d,queue_retry_data,delete_queue, automate_post
from Data_Manager.image_finder import get_image
from start import index, upload_photo, register_page, queues_page, queue_details, dashboard, publish, follow, auto_page, do_follow
from Django.tasks import save_schedule
from Data_Manager.text_ai import image_command, title_command
from Data_Manager.instagram_session import register, sessions_list, edit_session_list,relogin,delete_session
from Data_Manager.follow_instagram import follow_instagram_login, getting_user_id, showing_instagram_followers, showing_instagram_extractors_account
from Data_Manager.follow import follower_params
from Data_Manager.profile import profile_change, serve_profile_image, get_profile_picture, serve_user_profile_image
from Data_Manager.username import username_change
from Data_Manager.fullname import fullname_change
from django.urls import path, include


urlpatterns = [
    # Default Django admin urls (it has to be modified to sing new users easily)
    path('admin/', admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('', index, name='index'),
    
    # Display register page "register.html" for adding instagram's accounts
    path('register/', register_page, name='register'),
    # Retry login for instagram accounts(Displays on dashboard)
    path('relogin/', relogin, name='relogin'),
    # Submitting account register button on register page for instagram accounts
    path('submit_register/', register, name='submit_register'),
    # Fetches all Accounts details and objects
    path('insta_sessions/', sessions_list, name='insta_sessions_list'),
    # Edits account list
    path('edit_session_list/', edit_session_list, name='edit_session_list'),
    # Uploads photos for posting
    path('upload_photo/', upload_photo, name='upload_photo'),
    # It serves images from minio
    path('image/<path:path>/', serve_minio_image, name='serve_minio_image'),
    # It servers videos from minio
    path('video/<path:path>/', serve_minio_video, name='serve_minio_video'),
    # It posts stroies, post, reels based by imput paramteres
    path('publish_story/', publish_content, name='publish_content'),
    # If find Royalty Free images from Pixabay.com image website finder
    path('find_image/<str:keyword>', get_image, name='find_image'),
    # It gets instagram accounts objects and check their health
    path('clients/', clients, name='get_clients'),
    # It logs account details of how they are posting
    path('queue_log/', queue_log, name='queue_log'),
    # Display queues page "queues.html" to see how accounts posted/posting contents
    path('queues/', queues_page, name='queues'),
    # it logs accounts details of how they are posting
    path('queue_d/', queue_d, name='queue_d'),
    # it logs each accounts by details of how thery are posting contents
    path('queue_details/', queue_details, name='queue_details'),
    # it retries posting for accounts how have not been sucsessful to post content
    path('queue_retry/', queue_retry_data, name='queue_retry'),
    # it removes the selected queues
    path('delete_queue/<int:id>/', delete_queue, name='delete_queue'),
    # Display dashboard page "dashboard/dashboard.html" to see the overal situation of the system
    path('dashboard/', dashboard, name='dashboard'),
    # Display publish page "publish/publish.html" features to posting
    path('publish/', publish, name='publish'),
    # Display follow page "follower/follow.html" features to following
    path('follow/', follow, name='follow'),
    # it starts to follow the peoples you've selected to fllow
    path('dofollow/', do_follow, name='do_follow'),
    # it removes the selected account from the list of accounts
    path('delete_session/', delete_session, name='delete_session'),
    # it adds a specific account that searches and capture ohter instagram ids on the world
    # NOTE: This account is not used to marketing, only for getting the isntagram ids in order
    # to follow them later.
    path('follow_instagram_login/', follow_instagram_login, name='follow_instagram_login'),
    # it gets userd ids of the accounts you want and captures them in DB so later
    # you can follow them by "do_follow" API.
    path('getting_user_id/', getting_user_id, name='getting_user_id'),
    # it fatches the followers of a specific account in instagram so you can follow them later
    path('showing_instagram_followers/', showing_instagram_followers, name='showing_instagram_followers'),
    # it displays the accounts which is extracting the user ids from instagram
    path('showing_instagram_extractors_account/', showing_instagram_extractors_account, name='showing_instagram_extractors_account'),
    # it takes some batch of account and some batch of accounts to follow and it starts
    # to follow them one by one on a time based period to keep them from banning 
    path('follower_params/', follower_params, name='follower_params'),
    # NOTE: This function is still on matining and not production ready
    path('automate_post/', automate_post, name='automate_post'),
    # NOTE: This function is still on matining and not production ready
    path('save_schedule/', save_schedule, name='save_schedule'),
    # Displays an html page: 'auto_page.html' 
    path('auto_page/', auto_page, name='auto_page'),
    # NOTE: This function is still on matining and not production ready
    path('image_command/', image_command, name='automate_post'),
    # NOTE: This function is still on matining and not production ready
    path('title_command/', title_command, name='automate_post'),
    # it changes the profile images of the accounts
    path('profile_change/', profile_change, name='profile_change'),
    # it changes the username of the accounts
    path('username_change/', username_change, name='username_change'),
    # it changes the fullname of the accounts
    path('new_fullname/', fullname_change, name='new_fullname'),
    # it serves the profile images of the accounts
    path('images/profile/<str:image_name>/', serve_profile_image, name='profile_image'),
    # it saves the profile images of the accounts in minio
    path('images/profile-user/<str:user_profile_image>/', serve_user_profile_image, name='user_profile_image'),
    # it gets the profile images of the accounts
    path('instagram/profile-picture/', get_profile_picture, name='get_profile_picture'),
]
