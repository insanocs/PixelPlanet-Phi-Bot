import asyncio
import json
import os
import time
from io import BytesIO

import disnake
import matplotlib.pyplot as plt
import requests
from disnake.ext import commands
from funcs import chunk, dataBase, template
from funcs.planet import PlanetHistory
from PIL import Image, ImageChops
from funcs.buttons.diffButton import DiffButton

canvasData = {
    "e": {
        "code": 0,
        "name": "earth",
        "link": "d",
        "palette": 0
    },
    "1": {
        "code": 7,
        "name": "1bit",
        "link": "w",
        "palette": 2
    },
    "m": {
        "code": 1,
        "name": "moon",
        "link": "m",
        "palette": 1
    }
}

paletteList = [[
    (0,0,0,0),
    (255,255,255,255),
    (228,228,228,255),
    (196,196,196,255),
    (136,136,136,255),
    (78,78,78,255),
    (0,0,0,255),
    (244,179,174,255),
    (255,167,209,255),
    (255,84,178,255),
    (255,101,101,255),
    (229,0,0,255),
    (154,0,0,255),
    (254,164,96,255),
    (229,149,0,255),
    (160,106,66,255),
    (96,64,40,255),
    (245,223,176,255),
    (255,248,137,255),
    (229,217,0,255),
    (148,224,68,255),
    (2,190,1,255),
    (104,131,56,255),
    (0,101,19,255),
    (202,227,255,255),
    (0,211,221,255),
    (0,131,199,255),
    (0,0,234,255),
    (25,25,115,255),
    (207,110,228,255),
    (130,0,128,255)
    ],
    [
    (0,0,0,0),
    (49,46,47,255),
    (99,92,90,255),
    (49,46,47,255),
    (99,92,90,255),
    (129,119,107,255),
    (198,181,165,255),
    (255,237,212,255),
    (150,86,122,255),
    (202,112,145,255),
    (96,67,79,255),
    (136,79,94,255),
    (175,101,103,255),
    (195,124,107,255),
    (221,153,126,255),
    (233,181,140,255),
    (198,139,91,255),
    (140,89,74,255),
    (94,68,63,255),
    (225,173,86,255),
    (248,207,142,255),
    (239,220,118,255),
    (206,190,85,255),
    (157,159,55,255),
    (114,121,43,255),
    (81,94,46,255),
    (69,100,79,255),
    (80,134,87,255),
    (187,209,138,255),
    (91,84,108,255),
    (106,113,137,255),
    (122,148,156,255),
    (174,215,185,255)
    ],
    [
    (0,0,0,0),
    (0,0,0,255),
    (255,255,255,255)
    ]]

def checkPalette(im, palette):
  # Get the width and height of the image
  width, height = im.size
  # Create a grayscale version of the image
  imgray = im.convert('LA').convert('RGBA') # convert   to RGBA
  # Get a flattened list of pixel values from the original image
  pixels = list(im.getdata())
  # Iterate through the pixels in the original image
  wrongPixels = 0
  for i, pixel in enumerate(pixels):
      # Check if the pixel value is in the palette
      if pixel not in palette:
          # Set the pixel to red
          pixels[i] = (255, 0, 0, 255)
          wrongPixels += 1
      else:
          # Set the pixel to transparent
          pixels[i] = (0, 0, 0, 0)
  
  # Set the pixel data in the modified image
  im.putdata(pixels)
  imgray.paste(im, (0,0), im)
  
  # Display the modified image
  
  print(f'Wrong pixels: {wrongPixels}')
  return wrongPixels, imgray


class Diff(commands.Cog):

  def __init__(self, client):
    self.client = client

  @commands.Cog.listener("on_slash_command_error")
  async def error_handler(self, interaction, error):
    if isinstance(error, commands.CommandOnCooldown):
      await interaction.response.send_message(
        f"You have to wait {error.retry_after:.1f} seconds before using that command again."
      )
    if isinstance(error, commands.MissingPermissions):
      await interaction.response.send_message(
        f"Only admins of a server can remove the template. And you don't seem to be one. (no ban_members permissions)",
        file=disnake.File("./media/noperms.gif"),
      )

  @commands.cooldown(1, 5)
  @commands.slash_command(name='add',
                          description='Adds a template to your faction.')
  async def add(
    self,
    inter: disnake.ApplicationCommandInteraction,
    name: str,
    canvas: str,
    x: int,
    y: int,
    image_link: str,
  ):
    canvasList = ["earth", "1bit", "moon"]
    for key, canvasInfo in canvasData.items():
      if canvasInfo["name"] == canvas:
          canvasAbbreviation = key
          canvasCode = canvasInfo["code"]
          canvas_link = canvasInfo["link"]
          palette = paletteList[canvasInfo["palette"]]
          break
      else:
        pass

    print(f"[CONSOLE] New template being added from: {inter.guild.name}")
    # Checar se o comando tá certo
    if "_" in name:
      await inter.response.send_message(
        f"Sorry. You can't use _(underline) in your template name.")
      print(
        '[ERROR] User added template name with "_"(underline). Stopping operation'
      )
      return
    # Checar se o comando tem um canvas existente
    try:
      # Checar se o comando tem x e y válidos
      print(f"x:{x},y:{y}")
      x = int(x)
      y = int(y)
      print(f"x:{type(x)},y:{type(y)}")
      if abs(x) >> 32768 or abs(y) >> 32768:
        await inter.response.send_message(
          f"Coordinates can't be higher than 32768 or lower than -32768")
        return
      try:
        url = image_link
        print(f"[CONSOLE] Found url: {url}")
        response = requests.get(url, stream=True)
        imgTemp = Image.open(BytesIO(response.content)).convert("RGBA")
        imgTemp2 = Image.open(BytesIO(response.content)).convert("RGBA")
        await inter.response.send_message(
          f"Checking your palette."
        )
        wrongPixels, imgray = checkPalette(imgTemp, palette)
        
        if wrongPixels != 0:
          with BytesIO() as image_binary:
            imgray.save(image_binary, 'PNG')
            image_binary.seek(0)
            await inter.edit_original_message(f"Looks like your template has {wrongPixels} pixels not matching the PixelPlanet's palette, you should fix them before adding, or they'll be forever marked as wrong.\nWrong pixels displayed as RED below:", file=disnake.File(fp=image_binary, filename='image.png'))
        else:
          saveResult = template.saveTemplate(name, imgTemp2,
                                             [str(x), str(y)], canvasAbbreviation,
                                             inter.guild.id)
          if saveResult == 0:
            await inter.edit_original_message(
              "Seems like your faction still need a setup. Use /setup (name)"
            )
          elif saveResult == 1:
            await inter.edit_original_message(
              "Another template has already been created with that name.")
          elif saveResult == 2:
            await inter.edit_original_message(
              f"Template successfully created as {name}")
            print(f"Template created as {name} for {inter.guild.id}")
      except IndexError as e:
        await inter.response.send_message(
          f"Sorry I couldn't find your image. Try attaching it to a discord message and linking it on the command.'"
        )
      except IOError as e:
        await inter.response.send_message(
          f"Cannot identify your image, check if the link ends with .png or if the image is corrupt (you can try opening the link and checking in the browser)"
        )
      except Exception as e:
        await inter.response.send_message(
          f"Something weird happened. Report it at the support discord."
        )
    except ValueError as e:
      await inter.response.send_message(
        f"Looks like your X or/and Y aren't numbers.")
      print(f"[ERROR] X and Y arguments must be numbers. {e}")
      return
    except Exception as e:
      await inter.response.send_message(
        f"Something seems to have gone wrong. Report it at the support discord please.")
      print(f"[ERROR] X and Y arguments must be numbers. {e}")
      return

  #@commands.cooldown(1, 5)
  #@commands.slash_command(description='Updates your template. Needs admin perms.')
  #@commands.has_permissions(ban_members=True, kick_members=True)
  #async def update(self, inter: disnake.ApplicationCommandInteraction, name: str):
  #    userid = inter.guild.id
  #    username = inter.user.name
  #    print(f"[CONSOLE] Starting Update command for {username}: {name}")
  #    view = UpdateButton()
  #    await inter.response.send_message(f'What would you like to change in ***{name}*** template?', view=view)

  @commands.cooldown(1, 5)
  @commands.slash_command(
    description=
    'Removes a template from your faction. Needs admin perms in the server.')
  @commands.has_permissions(ban_members=True, kick_members=True)
  async def remove(self, inter: disnake.ApplicationCommandInteraction,
                   name: str):
    if len(name.split(" | ")) == 1:
      name = name.split(" | ")[0]
    elif len(name.split(" | ")) >= 2:
      name = name.split(" | ")[1]
    userid = inter.guild.id
    username = inter.user.name
    print(f"[CONSOLE] Started Remove command for {username}: {name}")
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templateArr = [
      temp.split("_") for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1].startswith(f"{name}")
    ]
    fileName = [
      temp for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1].startswith(f"{name}")
    ]
    #_n, tempName, x, y, canvas, fileFormat = templateArr[0]
    print(
      f'[CONSOLE] Deleting template {name} for {username} in {inter.guild.name}'
    )
    os.remove(f"./factions/{guildFolders[0]}/{fileName[0]}")
    await inter.response.send_message(
      f'Template ***{name}*** is no more. Its configs were: \n***X***: {templateArr[0][2]}, ***Y***: {templateArr[0][3]}.',
      ephemeral=False)

  @commands.cooldown(1, 15)
  @commands.slash_command(
    description='See statistics about your template in PixelPlanet.')
  async def diff(self, inter: disnake.ApplicationCommandInteraction,
                 name: str):
    if len(name.split(" | ")) == 1:
      name = name.split(" | ")[0]
    elif len(name.split(" | ")) >= 2:
      name = name.split(" | ")[1]
    userid = inter.guild.id
    username = inter.user.name
    print(
      f"[CONSOLE] Started Diff command for {username}: {name}, on {inter.guild.name} ({inter.guild.id})"
    )
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templateArr = [
      temp.split("_") for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1] == name
    ]
    fileName = [
      temp for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1].startswith(f"{name}")
    ]

    tempName, x, y, canvas = templateArr[0][1], templateArr[0][2], templateArr[
      0][3], templateArr[0][4]
    print('comparing')
    tot, err, elapsed = await chunk.ImageManipulation.compareImg(
      inter,
      [int(x), int(y)],
      canvas,
      f"./factions/{guildFolders[0]}/{fileName[0]}",
      tempName,
      "diff",
    )
    if canvas == "e":
      canvasCode = 0
      canvasName = "earth"
      canvasLink = "d"
    elif canvas == "1":
      canvasCode = 7
      canvasName = "1bot"
      canvasLink = "w"
    elif canvas == "m":
      canvasCode = 1
      canvasName = "moon"
      canvasLink = "m"
    dataBase.writeNewNumeric(inter.guild.id, tempName, time.time(),
                             (tot - err))
    print(f"[CONSOLE] Unpacking .csv data")
    processed_data = dataBase.readNumericData(inter.guild.id, tempName)

    pixel_rate = (processed_data[-2] - processed_data[-4]) / (
      (processed_data[-1] - processed_data[-3]) / 60 / 60)
    if round(pixel_rate) == 0:
      expected_time = f"This is not going anywhere. 0 px/h"
    if pixel_rate > 0:
      expected_time = f'{(tot/pixel_rate) if (tot/pixel_rate) < 36 else (tot/pixel_rate/24):.2f} {"hours" if (tot/pixel_rate) < 36 else "days"} to completion.'
    if pixel_rate < 0:
      expected_time = f'{(tot/pixel_rate) if abs(tot/pixel_rate) < 36 else (tot/pixel_rate/24):.2f} {"hours" if abs(tot/pixel_rate) < 36 else "days"} to destruction. (ouch!)'

    xx = []
    diffs = 0
    for i in range(0, 32):
      if (i % 2) != 0:  # SE É IMPAR
        if processed_data[i] == 0:
          pass
        else:
          xx.append((processed_data[32 - 1] - processed_data[i]) / 60 / 60)
          diffs = diffs + 1
      else:
        pass
    yy = []
    for i in range(0, len(processed_data)):
      if (i % 2) == 0:
        if processed_data[i + 1] == 0:
          pass
        else:
          yy.append(100 * processed_data[i] / tot)
      else:
        pass

    with plt.style.context("bmh"):
      print('plotting')
      plt.plot(xx, yy, "g-o")
      plt.fill_between(xx, yy, color='#30b61a', alpha=.2)
      plt.title(f"{tempName} percentage in the last {diffs} diffs")
      plt.xlim(max(xx), min(xx))
      plt.ylim(min(yy) - 5, max(yy) + 5)
      plt.ylabel("Percentage")
      plt.xlabel("Hours since this diff")
      plt.savefig("plot.png")
      plt.close()
    print("plot closed")
    embed = disnake.Embed(
      title="Teleport to coordinates",
      url=f"https://www.pixelplanet.fun/#{canvasLink},{x},{y},10",
      description=f"This took the bot {elapsed:.1f} seconds",
      color=0x00FF00,
    )
    embed.set_author(
      name="Template progress",
      url="https://www.google.com.br/",
      icon_url=
      "https://imgs.search.brave.com/fmspp-a8_pNrkOHAPi-HMfOFc_UfS0Pyc2lkHN5B8qQ/rs:fit:256:256:1/g:ce/aHR0cHM6Ly9leHRl/cm5hbC1wcmV2aWV3/LnJlZGQuaXQvUVhp/ejlLT0o1ODJFUlNw/MjNOWHVpSldzNjVS/dVRNa2JLWU1vbGx1/emNHVS5qcGc_YXV0/bz13ZWJwJnM9Zjdk/NjY0ZTJmNDM3OGI2/YjM2ZmFkMmY3M2U0/OTA1Y2U0MzU4NmVl/ZA",
    )
    embed.set_thumbnail(
      url=
      "https://cdn.discordapp.com/avatars/944655646157066280/95d8bee5622528bc2043982ace073924.png?size=256"
    )
    embed.add_field(
      name="Placed / Needed",
      value=f"{tot - err:,} / {tot:,} ({100*((tot-err)/tot):.1f}%)",
      inline=True,
    )
    embed.add_field(
      name="From last",
      value=
      f"{'+' if (processed_data[-2]-processed_data[-4]) > 0 else ''}{(processed_data[-2]-processed_data[-4]):,}",
      inline=True,
    )
    embed.add_field(
      name="Errors",
      value=f"{err:,}",
      inline=False,
    )
    embed.add_field(
      name="Pixel rate",
      value=
      f"{f'{round(pixel_rate)} px/h' if processed_data[-4] != 0 else 'NaN px/h'}",
      inline=False,
    )
    embed.add_field(name="Expected time at this rate",
                    value=f"{expected_time}",
                    inline=True)
    embed.set_footer(
      text=
      f"Last time this template was diffed: {time.ctime(processed_data[-3])}")
    embed.set_image(file=disnake.File("difference.png"))
    os.rename(
      f"./factions/{guildFolders[0]}/{fileName[0]}",
      f"./factions/{guildFolders[0]}/_{tempName}_{x}_{y}_{canvas}_{100*((tot-err)/tot):.1f}_.png"
    )
    view = DiffButton(
      f"https://www.pixelplanet.fun/#{canvasLink},{x},{y},10",
      f"./factions/{guildFolders[0]}/_{tempName}_{x}_{y}_{canvas}_{100*((tot-err)/tot):.1f}_.png",
      x, y, canvas)
    message = await inter.edit_original_message("Done!",
                                                embed=embed,
                                                view=view)
    view.message = message
    print("Command successful")
    await inter.wait()

  @commands.cooldown(1, 15)
  @commands.slash_command(
    description='See virgin pixels in the template that you wish.')
  async def virgin(self, inter: disnake.ApplicationCommandInteraction,
                   name: str):
    if len(name.split(" | ")) == 1:
      name = name.split(" | ")[0]
    elif len(name.split(" | ")) >= 2:
      name = name.split(" | ")[1]
    userid = inter.guild.id
    username = inter.user.name
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templateArr = [
      temp.split("_") for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1].startswith(f"{name}")
    ]
    fileName = [
      temp for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png") and temp.split("_")[1].startswith(f"{name}")
    ]
    tempName, x, y, canvas = templateArr[0][1], templateArr[0][2], templateArr[
      0][3], templateArr[0][4]
    virginpixels, elapsed = await chunk.compareImg(
      inter,
      [int(x), int(y)],
      f"./factions/{guildFolders[0]}/{fileName[0]}",
      tempName,
      "virgins",
    )
    embed = disnake.Embed(
      title=f"{tempName}",
      url=f"https://www.pixelplanet.fun/#d,{x},{y},10",
      description=f"This took the bot {elapsed:.1f} seconds",
      color=0x00FF00,
    )
    embed.set_author(
      name="Virgin pixels",
      url="https://www.google.com.br/",
      icon_url=
      "https://imgs.search.brave.com/fmspp-a8_pNrkOHAPi-HMfOFc_UfS0Pyc2lkHN5B8qQ/rs:fit:256:256:1/g:ce/aHR0cHM6Ly9leHRl/cm5hbC1wcmV2aWV3/LnJlZGQuaXQvUVhp/ejlLT0o1ODJFUlNw/MjNOWHVpSldzNjVS/dVRNa2JLWU1vbGx1/emNHVS5qcGc_YXV0/bz13ZWJwJnM9Zjdk/NjY0ZTJmNDM3OGI2/YjM2ZmFkMmY3M2U0/OTA1Y2U0MzU4NmVl/ZA",
    )
    embed.set_thumbnail(
      url=
      "https://cdn.discordapp.com/avatars/944655646157066280/95d8bee5622528bc2043982ace073924.png?size=256"
    )
    embed.add_field(name="Number of virgin pixels",
                    value=f"{virginpixels:,}",
                    inline=True)
    embed.set_image(file=disnake.File("virgins.png"))
    await inter.edit_original_message(embed=embed)

  #@commands.cooldown(1, 5)
  #@commands.slash_command(description='Edits a template.')
  #@commands.has_permissions(ban_members=True, kick_members=True)
  #async def update(self, inter: disnake.ApplicationCommandInteraction, string: str):

  #@update.autocomplete("name")
  #async def virgincomplete(
  #    self, inter: disnake.ApplicationCommandInteraction, string: str
  #):
  #    string = string.lower()
  #    guildFolders = [
  #        filename
  #        for filename in os.listdir("./factions/")
  #        if filename.startswith(f"{inter.guild.id}")
  #    ]
  #    templates = [
  #        temp.split("_")[1]
  #        for temp in os.listdir(f"./factions/{guildFolders[0]}")
  #        if temp.endswith(".png")
  #    ]
  #    print(templates)
  #   return [lang for lang in templates if string in lang.lower()]

  @add.autocomplete("canvas")
  async def canvascomplete(self, inter: disnake.ApplicationCommandInteraction,
                           string: str):
    string = string.lower()
    canvaslist = ["earth", "1bit", "moon"]
    return [opt for opt in canvaslist if string in opt.lower()]

  @virgin.autocomplete("name")
  async def virgincomplete(self, inter: disnake.ApplicationCommandInteraction,
                           string: str):
    string = string.lower()
    canvas_dict = {"e": "earth", "1": "1bit", "m": "moon"}
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templates = [
      f'{temp.split("_")[5] if temp.split("_")[5] != ".png" else "0"}% | {temp.split("_")[1]} | {canvas_dict[temp.split("_")[4]]}'
      for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png")
    ]
    for i in range(0, len(templates)):
      for j in range(i + 1, len(templates)):
        if (float(templates[i].split(" | ")[0].replace('%', '')) < float(
            templates[j].split(" | ")[0].replace('%', ''))):
          temp = templates[i]
          templates[i] = templates[j]
          templates[j] = temp
    return [lang for lang in templates if string in lang.lower()][0:25]

  @remove.autocomplete("name")
  async def namecomplete(self, inter: disnake.ApplicationCommandInteraction,
                         string: str):
    string = string.lower()
    canvas_dict = {"e": "earth", "1": "1bit", "m": "moon"}
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templates = [
      f'{temp.split("_")[5] if temp.split("_")[5] != ".png" else "0"}% | {temp.split("_")[1]} | {canvas_dict[temp.split("_")[4]]}'
      for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png")
    ]
    for i in range(0, len(templates)):
      for j in range(i + 1, len(templates)):
        if (float(templates[i].split(" | ")[0].replace('%', '')) < float(
            templates[j].split(" | ")[0].replace('%', ''))):
          temp = templates[i]
          templates[i] = templates[j]
          templates[j] = temp
    return [lang for lang in templates if string in lang.lower()][0:25]

  @diff.autocomplete("name")
  async def namecomplete(self, inter: disnake.ApplicationCommandInteraction,
                         string: str):
    string = string.lower()
    canvas_dict = {"e": "earth", "1": "1bit", "m": "moon"}
    guildFolders = [
      filename for filename in os.listdir("./factions/")
      if filename.startswith(f"{inter.guild.id}")
    ]
    templates = [
      f'{temp.split("_")[5] if temp.split("_")[5] != ".png" else "0"}% | {temp.split("_")[1]} | {canvas_dict[temp.split("_")[4]]}'
      for temp in os.listdir(f"./factions/{guildFolders[0]}")
      if temp.endswith(".png")
    ]
    for i in range(0, len(templates)):
      for j in range(i + 1, len(templates)):
        if (float(templates[i].split(" | ")[0].replace('%', '')) < float(
            templates[j].split(" | ")[0].replace('%', ''))):
          temp = templates[i]
          templates[i] = templates[j]
          templates[j] = temp
    return [lang for lang in templates if string in lang.lower()][0:25]


def setup(client):
  client.add_cog(Diff(client))
