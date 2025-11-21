import types
from xmlrpc import client
from flask import Flask, request
from waitress import serve
from faker import Faker
import os
import logging
import random

app = Flask(__name__)
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)
fake = Faker()

@app.route("/querybq")
def getqueryresults():
  # query the chicagotaxi dataset in BigQuery and the average taxi fare
  from google.cloud import bigquery
  client = bigquery.Client()
  query = """
    SELECT AVG(fare) as average_fare
    FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
    WHERE fare IS NOT NULL
  """
  query_job = client.query(query)
  results = query_job.result()
  for row in results:
    average_fare = row.average_fare
  return f"The average taxi fare in Chicago is ${average_fare:.2f}"

@app.route("/listfiles")
def getListofFiles():
  # get a list of files in the Google Cloud  bucket named friday-demo-bucket
  from google.cloud import storage
  storage_client = storage.Client()
  bucket = storage_client.get_bucket("friday-demo-bucket")
  blobs = bucket.list_blobs()
  files = [blob.name for blob in blobs]
  return str(files)

@app.route("/getfunfact")
def getfunfact():
  # using gemini api, return a fun fact about Wayne State in Detroit
  from google import genai
  from google.genai import types
  
  # You must specify a project and location for Vertex AI
  project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

  client = genai.Client(
      vertexai=True
  )

  model = "gemini-2.5-flash-preview-09-2025"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text="""Give me a fun fact about Wayne State University in Detroit.""")
      ]
    ),
  ]
  
  generate_content_config = types.GenerateContentConfig(
    temperature = 0.5,
    top_p = 0.95,
    max_output_tokens = 65535,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )]
  )

  output=""
  for chunk in client.models.generate_content_stream(
    model = model,
    contents = contents,
    config = generate_content_config,
    ):
    if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
        continue
    output=output + chunk.text
  return(output)

@app.route("/")
def getRoot():
  return "ROI Training Demo Main Page is Working!\n"

@app.route("/headers")
def show_headers():
  client_ip = request.remote_addr
  user_agent = request.headers.get('User-Agent')
  referer = request.headers.get('Referer')
  accept_language = request.headers.get('Accept-Language')
  all_headers = dict(request.headers)
  header_info = f"Your IP address is: {client_ip}<br\>" \
                f"Headers: {all_headers}"
  return header_info

@app.route("/random")
def getRandom():
  randomnum = random.randint(1, 100000000)/100
  return "Your Account Balance is $" + str(randomnum) + "!\n"

@app.route("/name")
def getRandomName():
  randomname = "Welcome attendee " + fake.name()
  return randomname

@app.route("/version")
def version():
  return "ROI Training Demo 1.5\n"

if __name__ == "__main__":
  serve(app,host="0.0.0.0",port=int(os.environ.get("PORT", 8080)))