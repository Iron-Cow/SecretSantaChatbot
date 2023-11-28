from aiogram.fsm.state import State, StatesGroup

class SecretSantaStates(StatesGroup):
    join_group = State()
    add_player = State()
    add_pair = State()

if __name__ == '__main__':
    print(AccountStates.password_enter)