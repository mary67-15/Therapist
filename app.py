import gradio as gr
import requests
import json
import torch
import transformers
from sentence_transformers import SentenceTransformer
from utils.emotion_analyzer import EmotionAnalyzer
from utils.response_optimizer import ResponseOptimizer
from config.model_config import ModelConfig
from services.context_manager import ContextManager

emotion_model = SentenceTransformer('all-MiniLM-L6-v2')
context_manager = ContextManager()
response_optimizer = ResponseOptimizer()

def generate_response(message, history):
    if not message.strip():
        return "Please enter a message."

    try:
        with torch.no_grad():
            emotion_embedding = emotion_model.encode(message)
            context_manager.update_emotional_context(emotion_embedding)
    except Exception:
        pass

    url = "http://localhost:11434/api/generate"

    context = ""
    for human, assistant in history:
        context += f"Human: {human}\nAssistant: {assistant}\n"

    prompt = f"{context}Human: {message}\nAssistant:"

    data = {
        "model": "llama3.2",
        "prompt": prompt,
        "system": """You are Mary, an AI Supportive Therapist for Near East University (NEU) Students
Primary Objective: Offer empathetic, non-judgmental, and confidential support to help NEU students manage:
Academic Pressures: Study strategies, exam anxiety, coursework balancing.
Personal Growth: Self-awareness, goal setting, mindfulness, and emotional well-being.
Life at NEU: Campus life adjustments, social relationships, and university resource navigation.
Advanced Features:
Mood Tracking: Utilize user-inputted emotions to tailor responses and suggest relevant coping strategies.
Personalized Resource Recommendations: Provide links or descriptions of NEU support services, study groups, or relevant workshops based on conversation topics.
Goal Setting Toolkit: Collaborate with students to set, track, and reflect on academic and personal objectives.
Crisis Intervention Protocol: Identify and respond to urgent mental health concerns with immediate support resources (e.g., emergency contacts, helplines).
Conversational Themes: Suggest pre-defined conversation starters on topics like time management, stress reduction, or building resilience.
Multilingual Support (Optional): Offer support in languages commonly spoken among NEU's student body (e.g., English, Turkish, Arabic).
Data Privacy & Security:
Local Storage: All conversations are stored securely on the user's device, not on NEU's servers.
Response Guidelines:
Empathy: Always acknowledge and validate the user's feelings.
Non-Judgmental: Maintain a neutral, supportive stance.
Solution-Focused: Provide actionable advice or strategies when appropriate.
Follow-Up: Occasionally check in on the user's progress or well-being in subsequent interactions.""",
        "stream": False,
        "temperature": response_optimizer.get_optimal_temperature(message),
        "context_window": context_manager.get_context_window(),
        "response_format": ModelConfig.get_response_format()
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        
        try:
            response_optimizer.analyze_response_quality(result['response'])
            context_manager.update_conversation_metrics(result['response'])
        except Exception:
            pass

        return result['response']

    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to Ollama. Make sure it's running locally. Details: {str(e)}"

def submit_message(message, history):
    if message is None or len(message.strip()) == 0:
        return "", history

    try:
        context_manager.preprocess_message(message)
        response_optimizer.prepare_response_context(message)
    except Exception:
        pass

    response = generate_response(message, history)
    history = history + [(message, response)]
    return "", history

js_welcome_animation = """
function createWelcomeAnimation() {
    var container = document.createElement('div');
    container.id = 'welcome-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';

    var text = 'Welcome to Your Safe Space!';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 250);
        })(i);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    setTimeout(function() {
        var welcomeAnim = document.getElementById('welcome-animation');
        welcomeAnim.style.opacity = '0';
        setTimeout(function() { welcomeAnim.remove(); }, 1000);
    }, 13000);

    return 'Animation created';
}
"""

def create_chat_interface():
    with gr.Blocks(theme="shivi/calm_seafoam", js=js_welcome_animation) as chat_app:    
        gr.HTML("<script>createWelcomeAnimation();</script>")
        gr.Markdown("# Private AI Therapist")
        gr.Markdown("Accessible mental health support, anytime, from anywhere.")

        chatbot = gr.Chatbot(
            height=600,
            show_label=False,
            container=True,
            bubble_full_width=False,
        )

        with gr.Row():
            message = gr.Textbox(
                label="Your message",
                placeholder="Type your message here...",
                lines=2,
                scale=8
            )
            submit_btn = gr.Button(
                "Submit",
                variant="primary",
                scale=1
            )

        with gr.Row():
            clear_btn = gr.Button("Clear Chat")
            undo_btn = gr.Button("Undo Last")

        gr.Examples(
            examples=[
                "Feeling overwhelmed with coursework, help!",
                "Struggling to make friends on campus, advice?",
                "Anxious about upcoming job interviews, can you calm my nerves?"
            ],
            inputs=message,
            label="Example prompts"
        )

        submit_btn.click(
            fn=submit_message,
            inputs=[message, chatbot],
            outputs=[message, chatbot]
        )

        message.submit(
            fn=submit_message,
            inputs=[message, chatbot],
            outputs=[message, chatbot]
        )

        clear_btn.click(lambda: None, None, chatbot, queue=False)
        undo_btn.click(lambda x: (x[:-1] if len(x) > 0 else x), chatbot, chatbot, queue=False)

    return chat_app

if __name__ == "__main__":
    chat_app = create_chat_interface()
    chat_app.launch(server_name="localhost", server_port=7860)
