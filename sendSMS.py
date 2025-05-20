from twilio.rest import Client

def send(message):
    # Twilio credentials (replace with your actual credentials)
    account_sid = 'your ssid'
    auth_token = 'your auth token'
    client = Client(account_sid, auth_token)

    # Replace with your Twilio phone number and recipient's number
    message = client.messages.create(
        body=message,
        to='recivers number', #fill in appropriately
        from_='senders number'  # Recipient's phone number

    )

    print("SMS sent: ", message.sid)
