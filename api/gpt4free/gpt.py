from typing import Any
import g4f
from g4f.client import AsyncClient

class DialogGPT:
    messages = dict()

    def __init__(self, id):
        self.id = id
        if self.id not in self.messages:
            self.messages[self.id] = [
                {"role": "user", "content": "Общайся со мной как будто ты русская девушка и я твой парень"},
                {"role": "assistant", "content": "Хорошо любимый!"}]

    async def gptDialog(self, mes: list):
        client = AsyncClient(
            provider=g4f.Provider.FreeGpt,
        )

        response = await client.chat.completions.create(
            model=g4f.models.gpt_4_turbo,
            messages=mes
        )

        return response.choices[0].message.content

    async def createDialog(self, message):
        print(message)
        self.messages[self.id].append({"role": "user", "content": message})

        answer = await self.gptDialog(mes=self.messages[self.id])

        self.messages[self.id].append({"role": "assistant", "content": answer})
        print(answer)
        return answer
