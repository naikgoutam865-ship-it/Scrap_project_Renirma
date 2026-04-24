from django.shortcuts import render
from django.http import JsonResponse
import json
from groq import Groq
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import AIKnowledge

User = get_user_model()
client = Groq(api_key=settings.GROQ_API_KEY)


def ask_assistant(request):

    if request.method == "POST":

        data = json.loads(request.body)
        question = data.get("question", "").lower().strip()

        # =========================
        # SESSION MEMORY
        # =========================
        if "chat_history" not in request.session:
            request.session["chat_history"] = []

        request.session["chat_history"].append({
            "role": "user",
            "content": question
        })

        # =========================
        # 1️⃣ DATABASE USER LOOKUP
        # =========================
        name = question.replace("who is", "").replace("kaun hai", "").strip()
        db_user = User.objects.filter(username__iexact=name).first()

        if db_user:
            role = getattr(db_user, "role", "user")
            reply = f"{db_user.username} is registered on ReNirma as a {role}."
            return JsonResponse({"reply": reply})

        # =========================
        # 2️⃣ KNOWLEDGE RETRIEVAL (FIRST!)
        # =========================
        stored = AIKnowledge.objects.filter(key__iexact=name).first()

        if stored:
            reply = f"{stored.key.title()} is {stored.value}"
            return JsonResponse({"reply": reply})

        # =========================
        # 3️⃣ LEARNING MODE
        # =========================
        # learning mode — only store statements, not questions
        q_lower = question.lower().strip()

        if (
            " is " in q_lower
            and not q_lower.endswith("?")
            and not q_lower.startswith(("what", "who", "where", "when", "why", "how"))
        ):
            parts = question.split(" is ", 1)

            if len(parts) == 2:
                key = parts[0].strip().lower()
                value = parts[1].strip()

                AIKnowledge.objects.update_or_create(
                    key=key,
                    defaults={"value": value}
                )

                reply = "Got it 👍 I will remember that."
                return JsonResponse({"reply": reply})
        # =========================
        # 4️⃣ AI RESPONSE
        # =========================
        system_prompt = """
You are ReNirma Smart Assistant.

IMPORTANT KNOWLEDGE:

ReNirma is a web platform that converts scrap into artwork.

It connects:
• Users – who sell scrap
• Dealers – who buy scrap
• Artists – who turn scrap into art

Main features:
• Scrap listing & selling
• Scrap requests & approvals
• Artwork creation from scrap
• Artwork marketplace
• Wishlist & orders
• Smart AI price suggestion
• Smart assistant guidance

RULES:
• If user asks about Renirma, explain the platform (NOT the assistant)
• Always answer platform-related questions clearly
• Only talk about assistant if user explicitly asks about assistant

Be helpful, friendly and natural.
Keep replies short and clear.
"""

        history = request.session["chat_history"][-6:]

        messages_payload = [
            {"role": "system", "content": system_prompt}
        ] + history

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages_payload
            )

            reply = completion.choices[0].message.content

        except Exception as e:
            print("AI ERROR:", e)
            reply = "Assistant temporarily unavailable. Try again."

        return JsonResponse({"reply": reply})


def chat_page(request):
    return render(request, "chatbot/chat.html")
