'''
Created by Frederikme (TeetiFM)
'''

import random
from tinderbotz.session import Session
import time
from tinderbotz.helpers.constants_helper import *
import openai
import asyncio
import re

import torch
import clip
from PIL import Image
import requests
from io import BytesIO

# TODO: may want to host CLIP, since this is slow af on most computers
device = "cuda" if torch.cuda.is_available() else "cpu"
# model = None
# preprocess = None

model, preprocess = clip.load("ViT-B/32", device=device)
# def load_model():
    # global model, preprocess

def hotornot(image_url, gender):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    # image = Image.open(requests.get(url, stream=True).raw)
    # image = Image.fromarray(image.astype("uint8"), "RGB")

    image = preprocess(image).unsqueeze(0).to(device)
    positive_terms = [f'a hot {gender}', f'a beautiful {gender}', f'an attractive {gender}']
    negative_terms = [f'a gross {gender}', f'an ugly {gender}', f'a hideous {gender}']

    pairs = list(zip(positive_terms, negative_terms))

    def evaluate(terms):
        text = clip.tokenize(terms).to(device)

        with torch.no_grad():
            logits_per_image, logits_per_text = model(image, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()
            return probs[0]

    probs = [evaluate(pair) for pair in pairs]
    
    positive_probs = [prob[0] for prob in probs]
    negative_probs = [prob[1] for prob in probs]

    hotness_score = round((probs[0][0] - probs[0][1] + 1) * 50, 2)
    beauty_score = round((probs[1][0] - probs[1][1] + 1) * 50, 2)
    attractiveness_score = round((probs[2][0] - probs[2][1] + 1) * 50, 2)

    hot_score = sum(positive_probs)/len(positive_probs)
    ugly_score = sum(negative_probs)/len(negative_probs)
    composite = ((hot_score - ugly_score)+1) * 50
    composite = round(composite, 2)
    return composite, hotness_score, beauty_score, attractiveness_score


def remove_emojis(data):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return re.sub(emoj, '', data)

def generate_completions(prompt):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": prompt},
        ],
        max_tokens=50,
        temperature=0.9,
        n=5
    )
    return completion

def auto_message(session):
    new_matches = session.get_new_matches(amount=20, quickload=True)

    # loop through my new matches and send them the first message of the conversation
    for match in new_matches:
        # store name and chatid in variables so we can use it more simply later on
        session.store_local(match)
        # print("match:", match.get_dictionary())
        

        session.open_chat(match.get_chat_id())

        # completion = openai.Completion.create(
        # model="text-davinci-003",
        # prompt=prompt,
        # max_tokens=50,
        # temperature=0.9,
        # n=5
        # )
        id = match.get_chat_id()
        while True:
            prompt = f"You need to write a one-liner for Tinder."
            context = ""
            if len(match.passions) > 0:
                random_passion = random.randint(0, len(match.passions)-1) 
                # cleaned = [passion.replace("My", "Her") for passion in match.passions]
                # cleaned = [passion.replace("My", "Her") for passion in match.passions]
                context = " Her interests/passions includes:\n- " + "\n- ".join([match.passions[random_passion].replace("My", "Her")]) + "."
            if match.bio and len(match.bio) > 0:
                context = context + f' Her bio is: {match.bio}.\n\n'

            # prompt = prompt + "Synthesize the information from her bio to write a witty, provacative and attention grabbing pick-up one-liner (you dont have to use all of the information, just what you think will get you laid). Use informal, lower case as if you were texting them"
            # prompt = prompt + "Write a thirsty and attention grabbing pick-up one-liner for Tinder. Never address them by their name or social media usernames. Never use emojis. Use informal, lower case as if you were texting them. You're allowed to reference only one single thing from her bio, and only if it's sexual. Only use 50 characters total."

            prompt = prompt + context + "Write a provacative and attention grabbing pick-up one-liner. Use informal, lower case as if you were texting them. Reference only one fact from her bio and interests, and only if it's sexual. Never, ever reference more than one fact. Be subtle and not cheesy. Use sexual double entrendres. Emojis are forbidden. Only use 50 characters."

            print("Generating conversation starters from bio: ", context)
            completion = generate_completions(prompt)
            pickup_lines = completion.choices
            for index, line in enumerate(pickup_lines):
                print(f"Line {index+1}:", remove_emojis(line.message.content.replace("\"", "", 2)), "\n")
            # pickup_line = completion.choices[0].message.content
            # name = match.get_name()
            # send pick up line with their name in it to all my matches
            while True:
                # Format the match her/his name in your pickup line for a more personal approach.
                # message = pickup_line.format(name)
                user_input = input("Enter the number of the pick up line to send... (1-5).\nTo re-generate suggestions, type r\nTo skip to the next match, type s\n\n")

                if str(user_input) in ('r', 's', '1', '2', '3', '4', '5'):
                    break
                print("Invalid input.")
            if str(user_input) == 'r':
                print("Regenerating completions...\n\n")
                continue
            elif str(user_input) == 's':
                break
            else:
                line_index = int(user_input)
                pickup_line = remove_emojis(pickup_lines[line_index - 1].message.content.replace("\"", "", 2))
                print(f"Sending selected message: {pickup_line}...\n")
                session.send_message(chatid=id, message=pickup_line)
                break

        # send a funny gif
        #session.send_gif(chatid=id, gifname="")

        # send a funny song
        #session.send_song(chatid=id, songname="")

        # send instagram or other socials like facebook, phonenumber and snapchat
        #session.send_socials(chatid=id, media=Socials.INSTAGRAM, value="Fredjemees")

        # you can also unmatch
        #session.unmatch(chatid=id)


async def main():
    # creates instance of session
    session = Session()
    # Or if you want to use a proxy
    # AUTHORISED BY IP -> "HOST:PORT"
    # AUTHORISED BY USERNAME, PASSWORD -> "username:password@HOST:PORT"
    # session = Session(proxy="23.23.23.23:3128")

    # set location (Don't need to be logged in for this)
    # session.set_custom_location(latitude=50.879829, longitude=4.700540)
    
    # replace this with your own email and password!
    email = ""
    password = ""
    
    # login using your google account with a verified email!
    #session.login_using_google(email, password)

    # Alternatively you can login using facebook with a connected profile!
    session.login_using_facebook(email, password)

    # Alternatively, you can also use your phone number to login
    '''
    - country is needed to get the right prefix, in my case +32
    - phone_number is everything after the prefix (+32)
    NOTE: this is not my phone number :)
    '''
    #country = "Belgium"
    #phone_number = "479011124"
    #session.login_using_sms(country, phone_number)

    # spam likes, dislikes and superlikes
    # to avoid being banned:
    #   - it's best to apply a randomness in your liking by sometimes disliking.
    #   - some sleeping between two actions is recommended
    # by default the amount is 1, ratio 100% and sleep 1 second
    #session.like(amount=10, ratio="72.5%", sleep=1)
    #session.dislike(amount=1)
    #session.superlike(amount=1)
    
    # adjust allowed distance for geomatches
    # Note: PARAMETER IS IN KILOMETERS!
    #session.set_distance_range(km=150)

    # set range of prefered age
    #session.set_age_range(18, 55)

    # set interested in gender(s) -> options are: WOMEN, MEN, EVERYONE
    #session.set_sexuality(Sexuality.WOMEN)

    # Allow profiles from all over the world to appear
    #session.set_global(True)

    # Getting matches takes a while, so recommended you load as much as possible from local storage
    # get new matches, with whom you haven't interacted yet
    # Let's load the first 10 new matches to interact with later on.
    # quickload on false will make sure ALL images are stored, but this might take a lot more time
    # messaged_matches = session.get_messaged_matches(amount=20, quickload=True)
    # get already interacted with matches (matches with whom you've chatted already)
    # messaged_matches = session.get_messaged_matches()
    
    # # you can store the data and images of these matches now locally in data/matches
    # # For now let's just store the messaged_matches

    # Pick up line with their personal name so it doesn't look spammy
    OPEN_AI_KEY = ""
    openai.api_key = OPEN_AI_KEY

    # print(new_matches)
    # print(messaged_matches)
    user_input = ""
    while True:
        while True:
            user_input = input("Select from menu\n[a] Auto-swipe profiles\n[m] Message new matches\n[x] Exit\n")
            if str(user_input) in ('a', 'm', 'x'):
                break
            print("Invalid input.")
        # if str(user_input) in ('a', 'm', 'x'):
            # break
        if str(user_input) == 'm':
            auto_message(session)
        elif str(user_input) == 'a':
            # load_model()
            num_swipes = int(input("How many profiles do you want to swipe through? Enter a number: "))
            score_threshold = int(input("Above what threshold attractiveness to swipe on? Enter a number from 0-100: "))
            for _ in range(num_swipes):
                # get profile data (name, age, bio, images, ...)
                geomatch = session.get_geomatch(quickload=False)
                # store this data locally as json with reference to their respective (locally stored) images
                # session.store_local(geomatch)
                composite_sum = 0
                attractiveness_sum = 0
                hotness_sum = 0
                beauty_sum = 0
                
                print(f"Number of images: {len(geomatch.image_urls)}")
                if geomatch.image_urls and len(geomatch.image_urls) > 0:
                    # TODO: change to get average score of all their images, defaults to using first photo, 
                    # figure out a way to get gender instead of assuming woman
                    for image_url in geomatch.image_urls:
                        composite, hotness_score, beauty_score, attractiveness_score = hotornot(image_url, "woman")
                        composite_sum += composite
                        attractiveness_sum += attractiveness_score
                        beauty_sum += beauty_score
                        hotness_sum += hotness_score
                    composite_avg = composite_sum/len(geomatch.image_urls)
                    attractiveness_avg = attractiveness_sum/len(geomatch.image_urls)
                    hotness_avg = hotness_sum/len(geomatch.image_urls)
                    beauty_avg = beauty_sum/len(geomatch.image_urls)
                    print(f"Average attractiveness scores:\nComposite ({composite_avg}), Hotness ({hotness_avg}), Beauty score ({beauty_avg}), Attractiveness ({attractiveness_avg})")
                is_hot = composite_sum != 0 and composite_avg >= score_threshold or attractiveness_avg >= score_threshold or hotness_avg >= score_threshold or beauty_avg >= score_threshold
                if composite_sum != 0 and is_hot:
                    print(f"Score is above {score_threshold}, swiping right\n")
                    session.smart_like()
                else:
                    print(f"Score is below threshold, swiping left\n")
                    session.dislike()
                    random_wait = random.randint(0, 2) 

        else:
            exit(1)
   
    # let's scrape some geomatches now

if __name__ == "__main__":
    asyncio.run(main())