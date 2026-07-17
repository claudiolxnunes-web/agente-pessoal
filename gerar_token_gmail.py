import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
flow = InstalledAppFlow.from_client_secrets_file('config/credentials.json', SCOPES)
flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

auth_url, _ = flow.authorization_url(prompt='consent')
print("\n>>> Abra este link no seu navegador, faca login e autorize:\n")
print(auth_url)
print("\n>>> Depois cole aqui o codigo que o Google mostrar:\n")

code = input("Codigo: ").strip()
flow.fetch_token(code=code)
creds = flow.credentials

with open('config/token_gmail.json', 'wb') as f:
    pickle.dump(creds, f)

print("\nToken salvo com sucesso em config/token_gmail.json!")
