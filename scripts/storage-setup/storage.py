import json
import os

from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"./eventito-key.json"

json_file_content_string = os.getenv("GCP_CREDENTIALS")

service_account_info = json.loads(json_file_content_string)
credentials = service_account.Credentials.from_service_account_info(service_account_info)


def create_bucket(bucket_name, storage_class="STANDARD", location="us-east1", has_public_urls=False):
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = storage_class

    bucket = storage_client.create_bucket(bucket, location=location)
    if has_public_urls:
        make_bucket_public(bucket)
    print(f"Bucket {bucket.name} successfully created.")


def make_bucket_public(bucket):
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append(
        {
            "role": "roles/storage.objectViewer",
            "members": {"allUsers"},
        }
    )
    bucket.set_iam_policy(policy)

    print(f"Bucket {bucket.name} is now public.")


def generate_signed_url_for_upload(bucket_name, blob_name, expiration=3600):
    client = storage.Client(credentials=credentials)

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(version="v4", expiration=expiration, method="PUT")

    return url


def generate_signed_url_for_read(bucket_name, blob_name, expiration=3600):
    client = storage.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(version="v4", expiration=expiration, method="GET")

    return url


def update_cors_policy(bucket_name):
    client = storage.Client()

    bucket = client.bucket(bucket_name)
    print("Los cors son:", bucket.cors)

    bucket.cors = [
        {
            "origin": ["https://eventito-frontend.vercel.app", "http://localhost:5173"],
            "method": ["PUT", "POST", "GET"],
            "responseHeader": ["Content-Type"],
            "maxAgeSeconds": 3600,
        }
    ]

    # bucket.cors = [
    #     {
    #     "origin": ["*"],
    #     "method": ["*"],
    #     "responseHeader": ["*"],
    #     "maxAgeSeconds": 3600
    #   }
    #     # {
    #     #     "origin": ["*"],
    #     #     "responseHeader": [
    #     #         "Content-Type",
    #     #         "x-goog-resumable"],
    #     #     "method": ['PUT', 'POST'],
    #     #     "maxAgeSeconds": 3600
    #     # }
    # ]

    bucket.patch()

    print(f"Set CORS policies for bucket {bucket.name} is {bucket.cors}")


# FOTO DE PERFIL
# LECTURA-> viene dentro del User con los GET (el campo se llama: profile_image_url)
# ESCRITURA -> Cuando se crea el usuario, creo el blob con una foto por defecto.
#           -> Para obtener la URL de MODIFICACIÓN, GET a /api/v1/users/{user_id}/upload_url/profile_image
# sin body que te devuelve el signed url.


# LAS URL EN GENERAL NO SE GUARDAN EN LA BASE DE DATOS, PORQUE SE HACEN FACIL CONCATENANDO, O SE GENERAN CIFRADAS.

# CONTENIDO ESTATICO DEL EVENTO
# LECTURA-> viene dentro del Evento con los GET (los campos se llaman: main_image_url, banner_image_url, brochure_url)
# ESCRITURA -> Cuando se crea el evento, creo el blob con una foto por defecto.
#           -> Para obtener la URL de MODIFICACIÓN, GET a /api/v1/events/{event_id}/upload_url/main_image; banner_image,
# brochure. una para cada sin body que te devuelve el signed url.

# GET
# LECTURA -> /api/v1/events/{event_id}/works/{work_id}/submissions/{submission_id}/read_url
# ESCRITURA -> /api/v1/events/{event_id}/works/{work_id}/submissions/{submission_id}/upload_url

# LECTURA -> /api/v1/events/{event_id}/works/{work_id}/reviews/{submission_id}/read_url
# ESCRITURA -> /api/v1/events/{event_id}/works/{work_id}/reviews/{submission_id}/upload_url

# LECTURA -> /api/v1/my-submissions/ -> traer todas las submissions del evento
#
#

# ESCRITURA -> lo vamos a hacer con url firmada (agregar restriccion de tamaño también)

# LECTURA -> PUBLICA (L1) o con URL CIFRADO (L2).


# fotos de perfil del usuario. -> 1 bucket todos archivos (L1)
# contenido estático del evento: banner, foto principal, pdf del evento folleto -> 1 bucket con carpeta por evento.
#  CARPETA tiene los 3. (L1)

# comprobantes -> carpeta por evento -> carpeta por usuario -> algunos tienen solo comprobante de pago, otros tienen
# tambien certificado (alumno regular x ejemplo).

# trabajos y correcciones -> carpeta por evento y subcarpetas submissions y revisiones
# -> subcarpeta por nombre de la entrega.

# create_bucket('eventito-profile_images')
# storage_client = storage.Client()

# bucket = storage_client.bucket('eventito-profile_images')

# make_bucket_public(bucket)

# url = generate_signed_url_for_upload('eventito-profile_image', 'image-user1.png')
# print(url)


def create_all_buckets():
    public_buckets = ["eventito-profile_images", "eventito-static_event_content"]
    private_buckets = ["eventito-payments_and_certificates", "eventito-submissions_and_reviews"]
    for bucket in public_buckets:
        create_bucket(bucket, has_public_urls=True)
    for bucket in private_buckets:
        create_bucket(bucket, has_public_urls=False)


# url = generate_signed_url_for_upload('eventito-profile_images', 'image.png')
# print(url)


create_all_buckets()
update_cors_policy("eventito-static_event_content")
