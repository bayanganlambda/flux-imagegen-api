import random
import time
import logging
import json
import requests

from urllib.parse import quote

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Utility: 
	@staticmethod
	def base36(n:int) -> str:
		""" Convert an integer to a base-36 string. """
		if n == 0:
			return '0'
		chars = '0123456789abcdefghijklmnopqrstuvwxyz'
		base36 = ''
		while n:
			n, r = divmod(n, 36)
			base36 = chars[r] + base36
		return base36
	
	@staticmethod
	def create_zx() -> int:
		# Generate a random integer in the range [0, 2147483647]
		random_int1 = random.randint(0, 2147483647)

		# Get the current timestamp in milliseconds
		current_timestamp = int(time.time() * 1000)

		# Perform XOR operation and take the absolute value
		xor_result = abs(random_int1 ^ current_timestamp)

		# Convert the results to base-36 strings
		base36_str1 = Utility.base36(random_int1)
		base36_str2 = Utility.base36(xor_result)

		# Concatenate the base-36 strings
		result = base36_str1 + base36_str2

		return result

	@staticmethod
	def create_rid(): 
		return int(1e5 * random.random())

	@staticmethod
	def stringify(data: dict, decode:bool = False) -> str: 
		data_string = json.dumps(data,separators=[",",":"])
		return quote(data_string, safe="()") if decode else data_string

	@staticmethod
	def print_json(data: dict, indent=2) -> str: 
		print(json.dumps(data, indent=indent))
		
class GoogleApi: 
	class Payload: 
		START_WRITE_SESSION="start_writesession"
		WRITE_ACCOUNT="write_account"

		@staticmethod
		def get(
			name: "Payload",
			token_id: str = "",
			local_id: str = "",
			stream_token: str = "GRBoQgKB9LW1",
			encode: bool = True
		): 
			payload = {"headers": {}}
			headers = payload["headers"]
			
			headers["X-Goog-Api-Client"] = "gl-js/ fire/10.12.2\r\n"
			headers["Content-Type"] = "text/plain\r\n"
			headers["X-Firebase-GMPID"] = "1:387174971425:web:4f1aa887d31c7bd4a1cb60\r\n"
			headers["Authorization"] = "Bearer %s\r\n" % (token_id)
			
			headers_encoded = "".join(quote("%s:%s" % (k,v), safe="") for k,v in headers.items())
			payload["headers"] = headers_encoded

			if name == GoogleApi.Payload.START_WRITE_SESSION: 
				payload["count"] = 1
				payload["ofs"] = 0
				
				req_data = [
					{
						"database": "projects/nightcafe-creator/databases/(default)"
					}
				]

				for index, value in enumerate(req_data): 
					payload["req%d___data__" % index] = Utility.stringify(value, decode=True)

			elif name == GoogleApi.Payload.WRITE_ACCOUNT: 
				payload["count"] = 3
				payload["ofs"] = 1

				req_data = [
					{
						"streamToken": stream_token,
						"writes": [
							{
								"update": {
									"name": f"projects/nightcafe-creator/databases/(default)/documents/users/{local_id}",
									"fields": {
										"id": {
											"stringValue": f"{local_id}"
										},
										"isAnonymous": {
											"booleanValue": True
										},
										"displayName": {
											"nullValue": "NULL_VALUE"
										}
									}
								},
								"updateMask": {
									"fieldPaths": [
										"displayName",
										"id",
										"isAnonymous"
									]
								},
								"updateTransforms": [
									{
										"fieldPath": "created",
										"setToServerValue": "REQUEST_TIME"
									},
									{
										"fieldPath": "updated",
										"setToServerValue": "REQUEST_TIME"
									}
								]
							}
						]
					},
					{
						"streamToken": stream_token,
						"writes": [
							{
								"update": {
									"name": f"projects/nightcafe-creator/databases/(default)/documents/users/{local_id}/safe/private",
									"fields": {
										"forceSignupAfterNCreations": {
											"integerValue": "1"
										}
									}
								},
								"updateMask": {
									"fieldPaths": [
										"forceSignupAfterNCreations"
									]
								},
								"updateTransforms": [
									{
										"fieldPath": "created",
										"setToServerValue": "REQUEST_TIME"
									},
									{
										"fieldPath": "updated",
										"setToServerValue": "REQUEST_TIME"
									}
								]
							}
						]
					},
					{
						"streamToken": stream_token,
						"writes": [
							{
								"update": {
									"name": f"projects/nightcafe-creator/databases/(default)/documents/users/{local_id}/safe/private",
									"fields": {
										"lastFBDetails": {
											"mapValue": {
												"fields": {}
											}
										}
									}
								},
								"updateMask": {
									"fieldPaths": [
										"lastFBDetails"
									]
								},
								"currentDocument": {
									"exists": True
								}
							}
						]
					}
				]

				for index, value in enumerate(req_data): 
					payload["req%d___data__" % index] = Utility.stringify(value, decode=True)

				del payload["headers"]

			if encode: 
				payload_encoded = "&".join(
					"%s=%s" % (k,v)
					for k, v in payload.items()
				)
				return payload_encoded
			
			return payload

	class Config: 
		API_KEY="AIzaSyD_bN4JwaaUIuYIOZ2cTvHrh0LRUYTXnfI"
		DATABASE="projects/nightcafe-creator/databases/(default)"
	
	class Url: 
		SIGN_UP="https://identitytoolkit.googleapis.com/v1/accounts:signUp"
		LOOK_UP = "https://identitytoolkit.googleapis.com/v1/accounts:lookup"
		WRITE_CHANNEL = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Write/channel"


	def sign_up(self): 
		token_id, local_id = self.generate_token()
		sid, gsessionid = self.start_writesession(token_id)
		write_account_data = self.write_account(local_id, gsessionid, sid)
		return token_id
		
	def generate_token(self): 
		requests_kwargs = { "url": self.Url.SIGN_UP, "params": { "key": self.Config.API_KEY }, "json": { "returnSecureToken": True } }
		try: 
			response = requests.post(**requests_kwargs)
			response.raise_for_status()

			if response.status_code == 200: 
				data = response.json()
				token_id = data["idToken"]
				local_id = data["localId"]
				return token_id, local_id
		except Exception as e: 
			logging.error(" at %s for %s" % (self.generate_token.__qualname__, e))
	
	def start_writesession(self, token_id:str): 
		requests_kwargs = {
			"url": self.Url.WRITE_CHANNEL,
			"params": {
				"VER": 8,
				"database": self.Config.DATABASE,
				"RID": Utility.create_rid(),
				"CVER": 22,
				"X-HTTP-Session-Id": "gsessionid",
				"zx": Utility.create_zx(),
				"t": 1
			},	
			"data": self.Payload.get(
				name=self.Payload.START_WRITE_SESSION,
				token_id=token_id
			)
		}

		try: 
			response = requests.post(**requests_kwargs)
			response.raise_for_status()

			if response.status_code == 200: 
				data = json.loads(response.text.split()[1])
				sid = data[0][1][1]
				gsessionid = response.headers.get("X-HTTP-Session-Id")
				return sid, gsessionid
		except Exception as e: 
			logging.error(" at %s for %s" % (self.start_writesession.__qualname__, e))
	
	def write_account(
			self, 
			local_id:str,
			gsessionid:str, 
			sid:str
		): 

		requests_kwargs = {
			"url": self.Url.WRITE_CHANNEL,
			"params": {
				"VER": 8,
				"database": self.Config.DATABASE,
				"gsessionid": gsessionid,
				"SID": sid,
				"RID": Utility.create_rid(),
				"AID": 1,
				"zx": Utility.create_zx(),
				"t": 1
			},	
			"data": self.Payload.get(
				name=self.Payload.WRITE_ACCOUNT,
				local_id=local_id,
			)
		}

		try: 
			response = requests.post(**requests_kwargs)
			response.raise_for_status()

			if response.status_code == 200: 
				return response.text
		except Exception as e: 
			logging.error(" at %s for %s" % (self.write_account.__qualname__, e))

class NightCafe: 
	class Url: 
		CREATIONS="https://api.nightcafe.studio/creations"
		CREATION="https://api.nightcafe.studio/creation"
		IMAGES="https://images.nightcafe.studio"

	class Payload: 
		@staticmethod
		def get(
			prompt: str,
			prompt_weights: int = 1,
			seed: int = 0,
			aspect_ratio: str = "1:1",
			num_images: int = 1,
			nsfw: bool = True
		): 
			payload = {"jobs": [{}]}
			jobs = payload["jobs"][0]

			jobs["context"] = { "type": "none" }
			jobs["jobType"] = "text"
			jobs["algorithm"] = "flux"
			jobs["formId"] = "text-to-image"
			jobs["preset"] = "none"
			jobs["prompts"] = [prompt]
			jobs["promptWeights"] = [prompt_weights]
			jobs["promptMagic"] = True
			jobs["fluxModel"] = "flux-dev"
			jobs["runtime"] = "short"
			jobs["resolution"] = "medium"
			jobs["seed"] = seed
			jobs["aspectRatio"] = aspect_ratio
			jobs["numImages"] = num_images
			jobs["injectNSFWNegatives"] = nsfw
		
			return payload
    
	class Headers: 
		@staticmethod
		def get(
			token: str
		): 
			headers = {}
			headers["x-auth-token"] = token

			return headers
	
	def __init__(self, token: str = None) -> None: 
		self.token = token
		self.quota = 0

		if not token: 
			self.sign_up()
	
	def sign_up(self): 
		if not self.quota: 
			gapi = GoogleApi()
			self.token = gapi.sign_up()
			self.quota = 5

	def random_seed(self): 
		seed = random.randint(0, 2**32 - 1)
		return seed
	
	def create(
		self,
		prompt: str,
		seed: int = 0,
		return_url: bool = False,
		**kwargs
	): 
		creation_result, generated_id = self.start_creation(prompt, seed, **kwargs)
		creation, jobs_path = self.get_creation(generated_id)
		img_url = "%s/%s" % (self.Url.IMAGES, jobs_path)

		if return_url: 
			return img_url

		try: 
			response = requests.get(img_url)
			response.raise_for_status()

			if response.status_code == 200: 
				return response.content
		except Exception as e: 
			logging.error(" at %s for %s" % (self.create.__qualname__, e))	


	def get_creation(self, generated_id: str): 
		requests_kwargs = { "url": "%s/%s" % (self.Url.CREATION, generated_id) }

		while True: 
			time.sleep(3)
			try: 
				response = requests.get(**requests_kwargs)
				response.raise_for_status()

				if response.status_code == 200: 
					data = response.json()
					if not data["job"].get("output"): 
						continue
					
					jobs_path = data["job"]["output"]
					return data, jobs_path
			except Exception as e: 
				logging.error(" at %s for %s" % (self.get_creation.__qualname__, e))	

	def start_creation(
		self,
		prompt: str,
		seed: int = 0,
		**kwargs
	): 
		self.sign_up()

		if not seed: 
			seed = self.random_seed()

		requests_kwargs = {
			"url": self.Url.CREATIONS,
			"json": self.Payload.get(prompt=prompt, seed=seed, **kwargs),
			"headers": self.Headers.get(token=self.token)
		}

		try: 
			response = requests.post(**requests_kwargs)
			response.raise_for_status()

			if response.status_code == 200: 
				self.quota -= 1
				data = response.json()
				generated_id = data["jobs"][0]["id"]

				return data, generated_id
		except Exception as e: 
			logging.error(" at %s for %s" % (self.start_creation.__qualname__, e))			

if __name__ == "__main__": 
	provider = NightCafe()
	prompt = "DisneyPixar"
	img = provider.create(prompt)
	
	if img: 
		from PIL import Image
		from io import BytesIO
		
		with Image.open(BytesIO(img)) as img_pil: 
			print("Image Result")
			img_pil.show()
	else: 
		print("Image Creation Has Been Failed!...")