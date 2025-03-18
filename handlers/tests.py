import asyncio
import time
import unittest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from .admin_handler import forwardMessage, SendMessageState  

class TestForwardBenchmark(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_state = AsyncMock()
        self.mock_message = MagicMock(spec=Message)
        self.mock_message.text = "📢 Guruhlarga"
        self.mock_message.answer = AsyncMock()

        # 1000 ta foydalanuvchi/guruh yaratamiz
        self.mock_users = [MagicMock(chat_id=i) for i in range(500)]
        self.mock_groups = [MagicMock(chat_id=-1000000000 - i) for i in range(500)]

    async def mock_get_users(self):
        return self.mock_users

    async def mock_get_groups(self):
        return self.mock_groups

    async def mock_forward(self, chat_id):
        await asyncio.sleep(0.001) 

    async def test_forward_message_benchmark(self):
        with unittest.mock.patch("database.models.User.get_private_users", new=self.mock_get_users), \
             unittest.mock.patch("database.models.Group.get_all_groups", new=self.mock_get_groups):

            forward_msg_mock = MagicMock()
            forward_msg_mock.forward = self.mock_forward
            self.mock_state.get_data.return_value = {"forward_message": forward_msg_mock}

            start_time = time.time()
            await forwardMessage(self.mock_message, self.mock_state)
            end_time = time.time()

            execution_time = end_time - start_time
            print(f"⏱️ 1000 ta xabarni forward qilish vaqti: {execution_time:.2f} soniya")

            self.assertLess(execution_time, 5, "Forward qilish juda sekin!")

if __name__ == "__main__":
    unittest.main()
