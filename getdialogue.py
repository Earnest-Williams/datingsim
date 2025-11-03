import random
import time
from script_loader import load_script


class Dialogue(object):
    def __init__(self):
        script = load_script()
        self.messages = script["dialogue"]
        self.date_choices = self.messages["date_choices"]

    def get_dialogue(self, engine, player):
        encounter_text = self.messages["encounter_message"].format(
            name=player.focus_character.name
        )
        print(f"\n        {encounter_text}\n")

        print(self.messages["greeting"])

        dialogue_tree = player.focus_character.dialogue_tree

        # dialogue trees loaded from the script use string keys ("0", "1", ...).
        # Iterate through the entries in key order while tolerating either
        # integer or string keys so the dialogue logic works regardless of the
        # source data format.
        ordered_dialogue_levels = sorted(
            dialogue_tree.items(),
            key=lambda item: int(item[0])
            if isinstance(item[0], str) and item[0].isdigit()
            else item[0],
        )

        for key, level in ordered_dialogue_levels:
            level_number = int(key) if isinstance(key, str) and key.isdigit() else key

            print(f"{self.messages['level_label']} {level_number}")
            print(f"{self.messages['opinion_label']} {player.focus_character.opinion}")

            print(self.messages["choice_prompt"])

            if player.focus_character.name not in player.known_girls:
                print(
                    1,
                    '-',
                    level["statement"]["compliment"],
                )
                print(
                    2,
                    '-',
                    level["statement"]["introduction"],
                    player.name,
                )
                print(
                    3,
                    '-',
                    level["statement"]["question"],
                )

                statement = input("> ")

                if int(statement) == 1:
                    print(level["reply"]["compliment"][0])
                    player.focus_character.opinion += level["reply"][
                        "compliment"
                    ][1]
                elif int(statement) == 2:
                    player.make_acquaintance(player.focus_character)
                    print(level["reply"]["introduction"][0])
                    player.focus_character.opinion += level["reply"][
                        "introduction"
                    ][1]
                elif int(statement) == 3:
                    print(level["reply"]["question"][0])
                    player.focus_character.opinion += level["reply"][
                        "question"
                    ][1]
            else:
                if player.focus_character.opinion < 3:
                    print(
                        1,
                        '-',
                        level["statement"]["compliment"],
                    )
                    print(
                        2,
                        '-',
                        random.choice(engine.current_location.observations),
                    )
                    print(
                        3,
                        '-',
                        level["statement"]["question"],
                    )

                    statement = input("> ")

                    if int(statement) == 1:
                        print(level["reply"]["compliment"][0])
                        player.focus_character.opinion += level["reply"][
                            "compliment"
                        ][1]
                    elif int(statement) == 2:
                        print(level["reply"]["observation"][0])
                        player.focus_character.opinion += level["reply"][
                            "observation"
                        ][1]
                    elif int(statement) == 3:
                        print(level["reply"]["question"][0])
                        player.focus_character.opinion += level["reply"][
                            "question"
                        ][1]

                else:
                    print(
                        1,
                        '-',
                        level["statement"]["compliment"],
                    )
                    print(
                        2,
                        '-',
                        random.choice(engine.current_location.observations),
                    )
                    print(
                        3,
                        '-',
                        level["statement"]["question"],
                    )
                    print(4, '-', self.messages["date_offer"])

                    statement = input("> ")

                    if int(statement) == 1:
                        print(level["reply"]["compliment"][0])
                        player.focus_character.opinion += level["reply"][
                            "compliment"
                        ][1]
                    elif int(statement) == 2:
                        print(level["reply"]["observation"][0])
                        player.focus_character.opinion += level["reply"][
                            "observation"
                        ][1]
                    elif int(statement) == 3:
                        print(level["reply"]["question"][0])
                        player.focus_character.opinion += level["reply"][
                            "question"
                        ][1]
                    elif int(statement) == 4:
                        print(self.messages["date_invite"])
                        for index, choice in enumerate(self.date_choices, start=1):
                            print(index, '-', choice["text"])

                        date_destination = input("> ")

                        print(self.messages["date_confirmation"])
                        time.sleep(0.3)

                        selected_choice = self.date_choices[int(date_destination) - 1]
                        engine.make_date(
                            engine.locations[selected_choice["location"]],
                            player.focus_character,
                        )

                        break

        engine.start_day()
