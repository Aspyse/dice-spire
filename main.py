import discord

intents = discord.Intents.default()
activity = discord.Activity(type=discord.ActivityType.listening, name="/help tricks")
bot = discord.Bot(activity=activity)

from dice import dice
bot.add_application_command(dice)

from help import help
bot.add_application_command(help)

from encounter import encounter
bot.add_application_command(encounter)

from utility import utility
bot.add_application_command(utility)

from chance import chance
bot.add_application_command(chance)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

if __name__ == '__main__':
    import config
    bot.run(config.token)