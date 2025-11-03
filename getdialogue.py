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
        print("\n        %s\n" % encounter_text)

        print(self.messages["greeting"])

        dialogue_tree = player.focus_character.dialogue_tree
        for i in range(len(dialogue_tree)):
            print(f"{self.messages['level_label']} {i}")
            print(f"{self.messages['opinion_label']} {player.focus_character.opinion}")

            print(self.messages["choice_prompt"])

            if player.focus_character.name not in player.known_girls:
                print(
                    1,
                    '-',
                    dialogue_tree[i]["statement"]["compliment"],
                )
                print(
                    2,
                    '-',
                    dialogue_tree[i]["statement"]["introduction"],
                    player.name,
                )
                print(
                    3,
                    '-',
                    dialogue_tree[i]["statement"]["question"],
                )

                statement = input("> ")

                if int(statement) == 1:
                    print(dialogue_tree[i]["reply"]["compliment"][0])
                    player.focus_character.opinion += dialogue_tree[i]["reply"][
                        "compliment"
                    ][1]
                elif int(statement) == 2:
                    player.make_acquaintance(player.focus_character)
                    print(dialogue_tree[i]["reply"]["introduction"][0])
                    player.focus_character.opinion += dialogue_tree[i]["reply"][
                        "introduction"
                    ][1]
                elif int(statement) == 3:
                    print(dialogue_tree[i]["reply"]["question"][0])
                    player.focus_character.opinion += dialogue_tree[i]["reply"][
                        "question"
                    ][1]
            else:
                if player.focus_character.opinion < 3:
                    print(
                        1,
                        '-',
                        dialogue_tree[i]["statement"]["compliment"],
                    )
                    print(
                        2,
                        '-',
                        random.choice(engine.current_location.observations),
                    )
                    print(
                        3,
                        '-',
                        dialogue_tree[i]["statement"]["question"],
                    )

                    statement = input("> ")

                    if int(statement) == 1:
                        print(dialogue_tree[i]["reply"]["compliment"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
                            "compliment"
                        ][1]
                    elif int(statement) == 2:
                        print(dialogue_tree[i]["reply"]["observation"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
                            "observation"
                        ][1]
                    elif int(statement) == 3:
                        print(dialogue_tree[i]["reply"]["question"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
                            "question"
                        ][1]

                else:
                    print(
                        1,
                        '-',
                        dialogue_tree[i]["statement"]["compliment"],
                    )
                    print(
                        2,
                        '-',
                        random.choice(engine.current_location.observations),
                    )
                    print(
                        3,
                        '-',
                        dialogue_tree[i]["statement"]["question"],
                    )
                    print(4, '-', self.messages["date_offer"])

                    statement = input("> ")

                    if int(statement) == 1:
                        print(dialogue_tree[i]["reply"]["compliment"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
                            "compliment"
                        ][1]
                    elif int(statement) == 2:
                        print(dialogue_tree[i]["reply"]["observation"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
                            "observation"
                        ][1]
                    elif int(statement) == 3:
                        print(dialogue_tree[i]["reply"]["question"][0])
                        player.focus_character.opinion += dialogue_tree[i]["reply"][
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
