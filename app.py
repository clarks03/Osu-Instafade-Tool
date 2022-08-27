import PySimpleGUI as sg
import os.path
import os
from PIL import Image, ImageDraw, ImageTk
import shutil

layout = [
    [sg.Text("Select a skin: "),
     sg.FolderBrowse("Browse", key="-INPUT-"),
     sg.Button("Submit")
     ]
]

window = sg.Window("osu! Skin Customizer", layout)


def getfile_insensitive(path):
    directory, filename = os.path.split(path)
    directory, filename = (directory or '.'), filename.lower()
    for f in os.listdir(directory):
        newpath = os.path.join(directory, f)
        if (os.path.isfile(newpath) or os.path.isdir(newpath)) and f.lower() == filename:
            return newpath, f

    return


def isfile_insensitive(path):
    return getfile_insensitive(path) is not None


def find_prefix(data: list, path: str) -> str:
    """Helper function of <find_data>. Returns the hitcircleprefix, if any.
    """
    for line in data:
        if b'HitCirclePrefix' in line:
            prefix = line.decode('utf-8').strip()
            prefix = prefix.removeprefix("HitCirclePrefix: ").strip()
            return prefix
    if os.path.isfile(path + "/default-0.png") or os.path.isfile(path + "/default-0@2x.png"):
        return "default"
    raise AttributeError


def find_if_above(data: list) -> bool:
    """Helper function of <find_data>. Returns HitCircleOverlayAboveNumber,
    if any.
    """
    for line in data:
        if b'HitCircleOverlayAboveNumber' in line:
            if_above = line.decode('utf-8').strip()
            if_above = if_above.removeprefix('HitCircleOverlayAboveNumber: ')
            if_above = if_above.strip()
            return True if if_above == "1" else False
    return True


def find_colours(data: list) -> list:
    """Helper function of <find_data>. Returns a list of colours,
    if any.
    """
    cols = []
    for line in data:
        if b'Combo' in line and (b'//' not in line or line.find(b'//') >
                                 line.find(b'Combo')):
            decoded = line.decode('utf-8')[line.find(b'Combo') + 5:]
            if not decoded[0].isdigit():
                continue
            decoded = decoded[1:]
            # we're going to find the index where the colours start
            index = 0
            while index < len(decoded):
                if decoded[index].isdigit():
                    break
                index += 1
            decoded = decoded[index:]

            col = decoded.strip().split(',')
            col = tuple(int(i.strip()[:3]) for i in col)
            cols.append(col)
    return [
        (255, 192, 0),
        (0, 202, 0),
        (18, 124, 255),
        (242, 24, 57)
    ] if len(cols) == 0 else cols


def find_data(path: str) -> dict:
    """Given the <path> of the skin (not skin.ini), we can search the skin.ini
    to find pieces of data. We are mainly interested in the following:
    -HitCirclePrefix (default if not found)
    -HitCircleOverlayAboveNumber (True if not found)
    -Combo Colours (Combo1, Combo2, Combo3, etc. if found,
        [(255, 192, 0), (0, 202, 0), (18, 124, 255), (242, 24, 57)] if not)
    """
    name = getfile_insensitive(path + "/skin.ini")[1]
    with open(f'{path}/{name}', "rb") as file:
        d = {}
        data = file.read().split(b'\n')
        try:
            d['HitCirclePrefix'] = find_prefix(data, path)
        except AttributeError:
            raise AttributeError
        d['HitCircleOverlayAboveNumber'] = find_if_above(data)
        d['Combo Colours'] = find_colours(data)
        return d


def get_hex(col: tuple) -> str:
    """Return the hex version of <col> (an rgb colour value).
    """
    return '#%02x%02x%02x' % col


def colorize_image(img: Image, col: tuple) -> Image:
    """Colorize the image at <path> given <col>.
    """
    overlay = Image.new(img.mode, img.size, col)
    color_flat = Image.blend(img, overlay, 1)

    transparent = Image.new(img.mode, img.size, (0, 0, 0, 0))
    transparent.paste(color_flat, (0, 0), img)

    return transparent


def remove_black_pixels(img: Image) -> None:
    """Remove all black pixels from <img>.
    """
    datas = img.getdata()

    new_data = []
    for item in datas:
        if item[0] == 0 and item[1] == 0 and item[2] == 0:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)


def make_image(path: str, col=None) -> list[Image]:
    """Make and return a list of image files of the hitcircle,
    hitcircleoverlay, and numbers on top of each other.
    """
    images = []
    
    try:
        num_path = find_data(path)["HitCirclePrefix"]
    except AttributeError:
        sg.popup("Skin does not have numbers.")
        return

    print(num_path)

    hitcircle_hd = os.path.isfile(path + "/hitcircle@2x.png")
    hitcircleoverlay_hd = os.path.isfile(path + "/hitcircleoverlay@2x.png")
    num_hd = os.path.isfile(path + "/" + num_path.lower() + "-0@2x.png")

    for i in range(10):
        if hitcircle_hd:
            hitcircle = Image.open(path + "/hitcircle@2x.png")
            if not all([hitcircleoverlay_hd, num_hd]):
                hitcircle = hitcircle.resize((int(hitcircle.size[0] / 2), int(hitcircle.size[1] / 2)))
        else:
            hitcircle = Image.open(path + "/hitcircle.png")

        hitcircle = hitcircle.resize((int(hitcircle.size[0] * 1.25), int(hitcircle.size[1] * 1.25)))
        
        remove_black_pixels(hitcircle)

        if col:
            hitcircle = colorize_image(hitcircle, col)

        if hitcircleoverlay_hd:
            hitcircleoverlay = Image.open(path + "/hitcircleoverlay@2x.png")
            if not all([hitcircle_hd, num_hd]):
                hitcircleoverlay = hitcircleoverlay.resize(
                    (int(hitcircleoverlay.size[0] / 2), int(hitcircleoverlay.size[1] / 2)))
        else:
            hitcircleoverlay = Image.open(path + "/hitcircleoverlay.png")

        hitcircleoverlay = hitcircleoverlay.resize((
                                                int(hitcircleoverlay.size[0] * 1.25),
                                                int(hitcircleoverlay.size[1] * 1.25)))

        remove_black_pixels(hitcircleoverlay)

        new_path = path + "/" + num_path.lower()

        if num_hd:
            num = Image.open(new_path + f"-{i}@2x.png")
            if not all([hitcircle_hd, hitcircleoverlay_hd]):
                num = num.resize((int(num.size[0] / 2), int(num.size[1] / 2)))
        else:
            num = Image.open(new_path + f"-{i}.png")
        
        if hitcircle.size[0] > hitcircleoverlay.size[0]:
            overlay_x = int(hitcircle.size[0] / 2 - hitcircleoverlay.size[0] / 2)
            overlay_y = int(hitcircle.size[1] / 2 - hitcircleoverlay.size[1] / 2)

            hitcircle.paste(hitcircleoverlay, (overlay_x, overlay_y), hitcircleoverlay)
        elif hitcircle.size[0] < hitcircleoverlay.size[0]:
            new_img = Image.new(hitcircle.mode, hitcircleoverlay.size, (0, 0, 0, 0))

            hitcircle_x = int(hitcircleoverlay.size[0] / 2 - hitcircle.size[0] / 2)
            hitcircle_y = int(hitcircleoverlay.size[1] / 2 - hitcircle.size[1] / 2)

            new_img.paste(hitcircle, (hitcircle_x, hitcircle_y), hitcircle)

            hitcircle = new_img

            hitcircle.paste(hitcircleoverlay, (0, 0), hitcircleoverlay)
        else:
            hitcircle.paste(hitcircleoverlay, (0, 0), hitcircleoverlay)

        num_x = int(hitcircle.size[0] / 2 - num.size[0] / 2)
        num_y = int(hitcircle.size[1] / 2 - num.size[1] / 2)

        hitcircle.paste(num, (num_x, num_y), num)

        images.append(hitcircle)

    return images


def if_hd(path: str) -> tuple:
    """Return a tuple of bools, corresponding to hitcircle_hd,
    hitcircleoverlay_hd, and num_hd, respectively.
    """
    num_path = find_data(path)['HitCirclePrefix'].lower()
    hitcircle_hd = os.path.isfile(path + "/hitcircle@2x.png")
    hitcircleoverlay_hd = os.path.isfile(path + "/hitcircleoverlay@2x.png")
    num_hd = os.path.isfile(path + "/" + num_path.lower() + "-0@2x.png")

    return hitcircle_hd, hitcircleoverlay_hd, num_hd


def generate_skin(path: str, hitcircle_hd: bool, hitcircleoverlay_hd: bool,
                  num_hd: bool, new_nums: list[Image], name: str, col: tuple) -> bool:
    """Create a new skin with name <name>. Delete the hitcircle, hitcircleoverlay,
    and nums as indicated by <hitcircle_hd>, <hitcircleoverlay_hd>, and
    <num_hd>, all of which determine whether said element is HD.

    (By delete, I mean make copies of all items as a 1x1 transparent image.)

    Next, I paste the new nums from <new_nums> to the nums directory, and
    edit the skin.ini to change HitCircleOverlap. If all items are HD, we 
    divide the size of the hitcircle by 2. If not, we take the size of the 
    hitcircle as our overlap.
    """
    # creating a new path
    new_path = path[:path.rfind('/')] + f"/{name}/"
    num_path = find_data(path)['HitCirclePrefix'].lower()

    # we need to create this directory before copying items to it.
    #    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    # now we copy to the directory
    try:
        shutil.copytree(path, new_path)
    except OSError:
        raise OSError("The file already exists.")

    # now i need to create some new files to replace the hitcircle and overlay.
    hitcircle = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    overlay = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    # now we delete the files.
    if os.path.isfile(new_path + "hitcircle@2x.png"):
        os.remove(new_path + "hitcircle@2x.png")
    if os.path.isfile(new_path + "hitcircle.png"):
        os.remove(new_path + "hitcircle.png")

    # also deleting slider elements 
    if os.path.isfile(new_path + "sliderstartcircle@2x.png"):
        os.remove(new_path + "sliderstartcircle@2x.png")
    if os.path.isfile(new_path + "sliderstartcircle.png"):
        os.remove(new_path + "sliderstartcircle.png")

    if os.path.isfile(new_path + "hitcircleoverlay@2x.png"):
        os.remove(new_path + "hitcircleoverlay@2x.png")
    if os.path.isfile(new_path + "hitcircleoverlay.png"):
        os.remove(new_path + "hitcircleoverlay.png")

    # also deleting slider elements 
    if os.path.isfile(new_path + "sliderstartcircleoverlay@2x.png"):
        os.remove(new_path + "sliderstartcircleoverlay@2x.png")
    if os.path.isfile(new_path + "sliderstartcircleoverlay.png"):
        os.remove(new_path + "sliderstartcircleoverlay.png")

    # now we save the files we made
    hitcircle.save(new_path + "hitcircle.png")
    overlay.save(new_path + "hitcircleoverlay.png")

    # now we delete the numbers
    for i in range(10):
        if os.path.isfile(new_path + num_path + f"-{i}@2x.png"):
            os.remove(new_path + num_path + f"-{i}@2x.png")
        if os.path.isfile(new_path + num_path + f"-{i}.png"):
            os.remove(new_path + num_path + f"-{i}.png")

        # we paste the number in its place 
        if all([hitcircle_hd, hitcircleoverlay_hd, num_hd]):
            new_nums[i].save(new_path + num_path + f"-{i}@2x.png")
        else:
            new_nums[i].save(new_path + num_path + f"-{i}.png")

    # finally, we need to edit the skin.ini file 

    name = getfile_insensitive(path + "/skin.ini")[1]

    with open(new_path + name, "rb") as file:
        data = file.readlines()

    line_index = -1
    fonts_index = 0
    for i, item in enumerate(data):
        if b'[Fonts]' in item:
            fonts_index = i
        if b'HitCircleOverlap' in item:
            line_index = i

            # if line_index is -1, that means it wasn't found. we can append it
    # after the fonts_index, which should always be found. 

    if line_index != -1:
        if all([hitcircle_hd, hitcircleoverlay_hd, num_hd]):
            size = int(new_nums[0].size[0] / 2)
            data[line_index] = b'HitCircleOverlap: ' + f'{size}\n'.encode()
        else:
            size = int(new_nums[0].size[0])
            data[line_index] = b'HitCircleOverlap: ' + f'{size}\n'.encode()
    else:
        if all([hitcircle_hd, hitcircleoverlay_hd, num_hd]):
            size = int(new_nums[0].size[0] / 2)
            data.insert(fonts_index + 1, b'HitCircleOverlap: ' + f'{size}\n'.encode())
        else:
            size = int(new_nums[0].size[0])
            data.insert(fonts_index + 1, b'HitCircleOverlap: ' + f'{size}\n'.encode())

    # i also want to remove all combo colours and replace it with (255, 255, 255).
    data_copy = data.copy()
    combo_1_index = -1
    colours_index = 0
    for i, item in enumerate(data):
        # checking for combo (we can copy and paste code here)
        if b'Combo' in item and (b'//' not in item or item.find(b'//') >
                                 item.find(b'Combo')):
            decoded = item.decode('utf-8')[item.find(b'Combo') + 5:]
            if not decoded[0].isdigit():
                continue
            if decoded[0] == '1':
                combo_1_index = i
            else:
                data_copy.remove(item)
        elif b'[Colours]' in item:
            colours_index = i

    if not col:
        col = (255, 255, 255)
    if combo_1_index != -1:
        data_copy[combo_1_index] = f'Combo1: {",".join(str(i) for i in col)}\n'.encode()
    else:
        data_copy.insert(colours_index + 1, f'Combo1: {",".join(str(i) for i in col)}\n'.encode())

    data = data_copy

    with open(new_path + name, "wb") as file:
        file.writelines(data)

    return True


while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break

    if event == "Submit":
        if isfile_insensitive(values['-INPUT-'] + '/skin.ini'):
            # right now I want to come up with a new window layout.
            # i want to have some skin-related options, such as being able
            # to use one of the existing combo colours as a hitcircle colour.
            # i'm gonna design something in paint.
            cols = find_data(values['-INPUT-'])['Combo Colours']
            skin_name = values['-INPUT-'][values['-INPUT-'].rfind('/') + 1:]
            new_layout = [
                [sg.Image(size=(128, 128), key="-IMAGE-")],
                [sg.Text("Name: "), sg.In(f"{skin_name} - instafade", key='-INPUT2-')],
                [sg.Radio('Use default colour', 'RADIO1', key='-DEFAULT-', default=True)],
                [sg.Radio('Use skin colour', 'RADIO1', key='-CUSTOM-')],
                [sg.Listbox([f'Combo{i + 1}' for i in range(len(cols))], size=(10, len(cols)), key='-LISTBOX-')],
                [sg.Button("Update"), sg.Button("Submit")]
            ]

            new_window = sg.Window("Customization", new_layout, finalize=True)
            listbox = new_window['-LISTBOX-'].Widget
            
            # get list of hitcircles
            circle_lst = make_image(values['-INPUT-'])

            curr_circle = circle_lst[0]
            image = ImageTk.PhotoImage(image=curr_circle)

            new_window['-IMAGE-'].update(data=image)

            for i in range(len(cols)):
                hex_col = get_hex(cols[i])
                listbox.itemconfigure(i, bg=hex_col)

            while True:
                event2, values2 = new_window.read()

                if event2 == sg.WIN_CLOSED:
                    break

                if event2 == "Update":
                    # we need to check if Use Skin Colour is on,
                    # and the colour chosen from the listbox.

                    if values2['-CUSTOM-']:
                        # colour value
                        if values2['-LISTBOX-']:
                            curr_col = values2['-LISTBOX-']
                            col = cols[int(curr_col[0][5]) - 1]
                            circle_lst = make_image(values['-INPUT-'], col)
                            image = ImageTk.PhotoImage(image=circle_lst[0])
                            new_window['-IMAGE-'].update(data=image)
                            new_window.refresh()
                        else:
                            sg.popup("No colour selected.")
                    else:
                        circle_lst = make_image(values['-INPUT-'])
                        image = ImageTk.PhotoImage(image=circle_lst[0])
                        new_window['-IMAGE-'].update(data=image)
                        new_window.refresh()

                if event2 == "Submit":
                    col = cols[int(values2['-LISTBOX-'][0][5]) - 1] if values2['-CUSTOM-'] else None
                    hitcircle_hd, hitcircleoverlay_hd, num_hd = if_hd(values['-INPUT-'])
                    try:
                        generate_skin(values['-INPUT-'], hitcircle_hd, hitcircleoverlay_hd,
                                      num_hd, circle_lst, values2['-INPUT2-'], col)
                        sg.popup("Skin created successfully!")
                    except OSError:
                        sg.popup("That file already exists!")

            new_window.close()

        else:
            sg.popup("Skin.ini not found.")

window.close()
