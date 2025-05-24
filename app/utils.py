async def send_welcome_message(client, user):
    """
    Send a welcome message to the user.
    """
    await client.send_message(
        "me",
        "Welcome to the Vacancy Collector Application! "
        "You are successfully connected.",
    )
