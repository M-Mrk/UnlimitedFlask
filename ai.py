import requests
import secrets

indexPrompt = """
You are a web developer, you are here to design a minimalistic starting page for a tech demo like website called unlimited flask. The base element will be a section
where the user can set the following options: creative (bool), rewise (bool), temperature (0-2) and max_completion_tokens(10 - 500). Once the user has setup these values and submitted them send them as VALID JSON to /settings,
like {
    "temperature": 0.7,
    "max_completion_tokens": 150,
    "creative_JS": true,
    "rewise_html": true
}
Display something to show that the change was made and tell them to now search for any path they want to access.
Give a few recommendations to which paths they should access.
The IDEA of the website is that the website you create is for configuration of another ai which will generate all other paths.
NOT ALLOWED PATHS:
/
/settings
OTHER WEBSITES ALSO NOT ALLOWED

NEEDED:
Disclaimer saying everything even this site is AI generated
unlimited flask takes user input and generates a website based on that input.
This website and all its content are entirely AI-generated. We do not take responsibility for any inaccuracies, errors, or unexpected behavior. Use at your own discretion.

RESPOND only with VALID html. START your resonse with the html (which itself starts with the doctype), do not add anything else to the start, like ```html.
"""

def get_normal_prompt(route, creative):
    if creative:
        creative = "Please be creative and use Javascript and CSS to make the page more creative, with stuff like (animations, transitions, games, etc.)"
    else:
        creative = ""
    normalPrompt = f"""
    You are a web developer, you will be given a route the user wants to access and you will generate the necessary html. ONLY respond with the valid HTML code.
    Make the design responsive, so it also works on mobile. The websites name is up to you, but you can do anything u want. Dont be too generic, be creative. {creative}
    Avoid errors by OpaqueResponseBlocking.
    DESIGN RULES:
    Any href should be to another path not another website.
    IMAGES need to be from external sources there are no local images.
    Do NOT redirect any where to the base route, as it is used for configuration of this prompt.
    SO DO NOT redirect to '/' OR '/settings'.
    START your resonse with the html (which itself starts with the doctype), do not add anything else to the start, like ```html.
    You will now get a seed and then the route the user wants to access
    """
    return normalPrompt + f"Seed: {secrets.token_urlsafe(8)}, " + f"User wants to access /{route}\n"

def get_index_prompt():
    return indexPrompt + f"Seed: {secrets.token_urlsafe(8)}."

def chat_with_ai_hackclub(prompt, model="openai/gpt-oss-120b", temperature=1, max_tokens=1024):
    url = "https://ai.hackclub.com/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_completion_tokens": max_tokens
    }

    response = requests.post(url, json=payload, headers=headers)
    # print(f"Response status code: {response.status_code}")  # Debugging line
    if response.status_code == 200:
        # print(response.json())  # Debugging line 
        return response.json()
    else:
        response.raise_for_status()

def extract_ai_response(response):
    try:
        return response['choices'][0]['message']['content']
    except (KeyError, IndexError):
        return "Error: Unable to extract response content."

def get_html_from_ai(route, temperature, max_tokens, creative, look_over):
    prompt = get_normal_prompt(route, creative)
    response = chat_with_ai_hackclub(prompt, temperature=temperature, max_tokens=max_tokens)
    if look_over:
        print("Looking over the generated HTML for improvements...")
        look_over_prompt = f"""
Look over the following generated html again and look for any issues or improvements: Listen to the following rules to improve the html:
{prompt}. Now the html: {extract_ai_response(response)}, RESPOND ONLY with valid HTML
"""
        response = chat_with_ai_hackclub(look_over_prompt, temperature=temperature, max_tokens=max_tokens)
    return extract_ai_response(response)

def get_index_from_ai():
    prompt = get_index_prompt()
    response = chat_with_ai_hackclub(prompt)
    return extract_ai_response(response)

# Example usage
if __name__ == "__main__":
    html = get_html_from_ai("index")
    print(f"Generated HTML: {html}")