import discord
from rolling_implementation import *
from roll_aliases import *

dice = discord.SlashCommandGroup("dice", "Dice and bag commands from Bag of Dice Holding")

@dice.command(description="Roll using dice notation.")
async def roll(ctx, dice: discord.Option(str)):
    outroll = await rollnotation(dice)
    await ctx.respond(f"{ctx.author.display_name}'s {outroll[0]}: `{outroll[1]}` = {outroll[2]}")

@dice.command(description="Save a die to your bag.")
async def save(ctx, alias: discord.Option(str), dice: discord.Option(str)):
    saveexit = await storedice(ctx.author.id, alias, dice)
    if saveexit == None:
        await ctx.respond(f"Sorry, you can't have more than 25 dice stored at once. Please free up your bag with `/deletedice`, or edit an existing die with `/editdice`.", ephemeral=True)
    else:
        await ctx.respond(f"Dice **{saveexit[0]}** saved: `{saveexit[1]}`", ephemeral=True)

@dice.command(description="Delete all saved dice.")
async def clear(ctx):
    clearview = discord.ui.View(timeout=120)
    yes = discord.ui.Button(label="Clear All Dice", operation=1)
    async def confirm(interaction):
        await deletealldice(interaction.user.id)
        await interaction.response.send_message(f"{interaction.user.display_name} dumped their dice bag.", ephemeral=True)
    yes.callback = confirm
    clearview.add_item(yes)

    no = discord.ui.Button(label="Cancel")
    async def cancel(interaction):
        await interaction.response.defer()
        await interaction.followup.edit_message(interaction.message.id, content="Cancelled deletion.", view=None)
    no.callback = cancel
    clearview.add_item(no)
    
    await ctx.respond("Are you sure you want to **delete all of your dice**?", view=clearview, ephemeral=True)

@dice.command(description="Open your bag of saved dice.")
async def bag(ctx):
    bagview = DiceBag(timeout=10)
    await bagview.create(ctx.user.id, operation=0)
    await ctx.respond(f"**{ctx.user.display_name}'s dice bag**", view=bagview, ephemeral=True)

class DiceBag(discord.ui.View):
    # needs to be async to use getdice from aiosqlite
    async def create(self, user, operation):
        saveddice = await getdice(user)
        for die in saveddice:
            self.add_item(DiceButton(label=die[1], command=die[2], operation=operation))
        if operation == 0:
            await self.addplusbutton()
        elif operation == 1:
            await self.adddonebutton("Deletion complete.")
        else:
            await self.adddonebutton("Editing complete.")

    async def addplusbutton(self):
        if len(self.children) < 25:
            addbutton = discord.ui.Button(emoji="➕")
            async def adddice(interaction):
                await interaction.response.send_modal(StoreModal(interaction.message.id, title="Save new dice"))
            addbutton.callback = adddice
            self.add_item(addbutton)

    async def adddonebutton(self, content):
        donebutton = discord.ui.Button(label="Done")
        async def done(interaction):
            await interaction.response.defer()
            await interaction.followup.edit_message(interaction.message.id, content=content, view=None)
        donebutton.callback = done
        self.add_item(donebutton)

class DiceButton(discord.ui.Button):
    # does not need to be async as long as callback is awaited
    def __init__(self, command, operation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = command
        if operation == 0:
            self.style = discord.ButtonStyle.green
            self.callback = self.add_callback
        elif operation == 1:
            self.style = discord.ButtonStyle.red
            self.callback = self.delete_callback
        else:
            self.style = discord.ButtonStyle.blurple
            self.callback = self.edit_callback
    
    async def add_callback(self, interaction):
        outroll = await rollnotation(self.command)
        #SHOULD NOT BE EPHEMERAL
        await interaction.response.send_message(f"{interaction.user.display_name}'s **{self.label}** ({self.command}): `{outroll[1]}` = {outroll[2]}")

    async def delete_callback(self, interaction):
        confirmation = discord.ui.View(timeout=120)
        yes = discord.ui.Button(label="Delete", style=discord.ButtonStyle.red)
        async def confirm(confirminteraction):
            await removedice(confirminteraction.user.id, self.label)
            await confirminteraction.response.defer()

            deleteview = DiceBag(timeout=120)
            await deleteview.create(interaction.user.id, operation=1)
            if len(deleteview.children) > 1:
                await confirminteraction.followup.edit_message(interaction.message.id, view=deleteview)
            else:
                await confirminteraction.followup.edit_message(interaction.message.id, content=f"{confirminteraction.user.display_name}'s dice bag is empty.", view=None)

            await confirminteraction.followup.edit_message(confirminteraction.message.id, content=f"**{self.label}** has been deleted.", view=None)   
        yes.callback = confirm
        confirmation.add_item(yes)

        no = discord.ui.Button(label="Cancel")
        async def cancel(confirminteraction):
            await confirminteraction.response.defer()
            await confirminteraction.followup.edit_message(confirminteraction.message.id, content="Cancelled deletion.", view=None)
        no.callback = cancel
        confirmation.add_item(no)
        
        await interaction.response.send_message(f"Are you sure you want to delete **{self.label}**?", view=confirmation, ephemeral=True)

    async def edit_callback(self, interaction):
        await interaction.response.send_modal(EditModal(alias=self.label, command=self.command, message=interaction.message.id, title="Edit dice values"))

class StoreModal(discord.ui.Modal):
    def __init__(self, message, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.message = message

        self.add_item(discord.ui.InputText(label="Name"))
        self.add_item(discord.ui.InputText(label="Dice Roll"))

    async def callback(self, interaction):
        saveexit = await storedice(interaction.user.id, self.children[0].value, self.children[1].value)
        await interaction.response.send_message(f"Dice **{saveexit[0]}** saved: `{saveexit[1]}`", ephemeral=True)

        bagview = DiceBag(timeout=120)
        await bagview.create(interaction.user.id, operation=0)
        await bagview.addplusbutton()
        await interaction.followup.edit_message(self.message, view=bagview)

@dice.command(description="Delete selected dice from bag.")
async def delete(ctx):
    deleteview = DiceBag(timeout=120)
    await deleteview.create(ctx.user.id, operation=1)
    if len(deleteview.children) > 1:
        await ctx.respond(f"**Deleting from {ctx.user.display_name}'s dice bag**", view=deleteview, ephemeral=True)
    else:
        await ctx.respond(f"{ctx.user.display_name}'s dice bag is empty.", ephemeral=True)

@dice.command(description="Edit existing dice from bag.")
async def edit(ctx):
    editview = DiceBag(timeout=120)
    await editview.create(ctx.user.id, operation=2)
    await ctx.respond(f"**Editing {ctx.user.display_name}'s dice**", view=editview, ephemeral=True)

class EditModal(discord.ui.Modal):
    def __init__(self, alias, command, message, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.alias = alias
        self.message = message

        self.add_item(discord.ui.InputText(label="Name", value=alias))
        self.add_item(discord.ui.InputText(label="Dice Roll", value=command))

    async def callback(self, interaction):
        await updatedice(interaction.user.id, self.alias, self.children[0].value, self.children[1].value)
        if self.alias == self.children[0].value:
            await interaction.response.send_message(f"Dice **{self.children[0].value}** updated: `{self.children[1].value}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"Dice **{self.alias}** updated to **{self.children[0].value}**: `{self.children[1].value}`", ephemeral=True)
        
        editview = DiceBag(timeout=120)
        await editview.create(interaction.user.id, operation=2)
        await interaction.followup.edit_message(self.message, view=editview)