import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.auth.manager import AuthManager


async def main():
    user, password = await AuthManager.create_user(sys.argv[1])
    print(f"Username: {user.username}, password: {password}")


if __name__ == "__main__":
    asyncio.run(main())
