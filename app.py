import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import threading


class OllamaChatbot:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Local Chatbot")
        self.root.geometry("600x700")

        # Model Selection
        self.model_label = tk.Label(root, text="Select Model:")
        self.model_label.pack(pady=(10, 0))

        self.model_combobox = ttk.Combobox(root, state="readonly")
        self.model_combobox.pack(padx=20, pady=10, fill=tk.X)

        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            width=70,
            height=30,
            state='disabled'
        )
        self.chat_display.pack(padx=20, pady=10)

        # Message Input
        self.message_entry = tk.Entry(root, width=70)
        self.message_entry.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.message_entry.bind('<Return>', self.send_message)

        # Send Button
        self.send_button = tk.Button(
            root,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(pady=(0, 20))

        # Chat history
        self.messages = []

        # Initialize the application
        self.fetch_models()

    def fetch_models(self):
        try:
            response = requests.get('http://localhost:11434/api/tags')
            models = [model['name'] for model in response.json().get('models', [])]

            if models:
                self.model_combobox['values'] = models
                self.model_combobox.set(models[0])
            else:
                self.display_message("No models found. Ensure Ollama is running.")

        except requests.RequestException as e:
            self.display_message(f"Error fetching models: {e}")

    def send_message(self, event=None):
        message = self.message_entry.get().strip()

        if not message:
            return

        selected_model = self.model_combobox.get()

        if not selected_model:
            self.display_message("Please select a model first.")
            return

        # Clear input
        self.message_entry.delete(0, tk.END)

        # Display user message
        self.display_message(f"You: {message}", 'user')

        # Start generation in a separate thread
        threading.Thread(
            target=self.generate_response,
            args=(selected_model, message),
            daemon=True
        ).start()

    def generate_response(self, model, message):
        try:
            # Add current conversation to messages
            conversation = self.messages + [
                {"role": "user", "content": message}
            ]

            response = requests.post(
                'http://localhost:11434/api/chat',
                json={
                    'model': model,
                    'messages': conversation,
                    'stream': False
                }
            )

            if response.status_code == 200:
                ai_response = response.json()['message']['content']

                # Update UI in main thread
                self.root.after(
                    0,
                    self.display_message,
                    f"AI: {ai_response}",
                    'ai'
                )

                # Update messages for context
                self.messages.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ai_response}
                ])

            else:
                self.root.after(
                    0,
                    self.display_message,
                    f"Error: {response.text}",
                    'error'
                )

        except Exception as e:
            self.root.after(
                0,
                self.display_message,
                f"Generation error: {e}",
                'error'
            )

    def display_message(self, message, tag=None):
        self.chat_display.configure(state='normal')

        # Add tag configurations
        self.chat_display.tag_config('user', foreground='blue')
        self.chat_display.tag_config('ai', foreground='green')
        self.chat_display.tag_config('error', foreground='red')

        # Insert message with appropriate tag
        self.chat_display.insert(tk.END, f"{message}\n", tag)

        # Autoscroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')


def main():
    root = tk.Tk()
    app = OllamaChatbot(root)
    root.mainloop()


if __name__ == "__main__":
    main()