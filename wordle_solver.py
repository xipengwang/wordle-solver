from enum import Enum
from typing import List
import copy
import logging
import math

class LetterStatus(Enum):
    Yes = 0
    Exist = 1
    No = 2

def WordLength(word_list : List[str]):
    assert word_list, "Empty list"
    ret = len(word_list[0])
    for word in word_list:
        assert len(word) == ret, f"{word} doesn't have length as {ret}"
    return ret


def GetWordStatus(*, guess_word : str, true_word : str):
    assert len(guess_word) == len(true_word)
    status = []
    for i, letter in enumerate(guess_word):
        if letter == true_word[i]:
            status.append(LetterStatus.Yes)
        elif letter in true_word:
            status.append(LetterStatus.Exist)
        else:
            status.append(LetterStatus.No)
    return status


def StatusToString(guess_word_status : List[LetterStatus], seperator=' '):
    return seperator.join([status.name for status in guess_word_status])


def DigitStringToWordStatus(status_str):
    word_status = []
    for s in status_str:
        if s == '0':
            word_status.append(LetterStatus.Yes)
        elif s == '1':
            word_status.append(LetterStatus.Exist)
        elif s == '2':
            word_status.append(LetterStatus.No)
        else:
            assert False, f"unrecognized number string {s} in {status_str}."
    return word_status


def CalculateWordScore(*, word_list : List[str], guess_word : str):
    status_frequency_dict = {}
    for word in word_list:
        status = GetWordStatus(guess_word=guess_word, true_word=word)
        status_str = StatusToString(status, '-')
        if status_str in status_frequency_dict:
            status_frequency_dict[status_str] += 1.0
        else:
            status_frequency_dict[status_str] = 1.0

    expected_entropy = 0
    p_sum = 0
    for (k, v) in status_frequency_dict.items():
        p = v / len(word_list)
        p_sum += p
        expected_entropy -= p * math.log2(p)
    return expected_entropy


def GenerateRankedCandidates(word_list : List[str]):
    ranked_candidates = []
    for i, word in enumerate(word_list):
        score = CalculateWordScore(word_list=word_list, guess_word=word)
        ranked_candidates.append((word, score))
        if i % 100 == 0:
            logging.debug(f"Processing {i}/{len(word_list)} word...")
    ranked_candidates.sort(reverse=True, key=lambda elem:elem[1])
    return ranked_candidates


def AllYes(guess_word_status):
    return all([status == LetterStatus.Yes for status in guess_word_status])


def PruneWordList(*, curr_word_list, guess_word, guess_word_status):
    new_word_list = []
    for word in curr_word_list:
        word_status = GetWordStatus(guess_word=guess_word, true_word=word)
        if StatusToString(word_status) == StatusToString(guess_word_status):
            new_word_list.append(word)
    assert len(new_word_list)!=0, "Sorry, our word list doesn't contain the True Word..."
    return new_word_list


class WordleSolver():
    def __init__(self, word_list : List[str], logging_level = logging.INFO):
        logging.basicConfig()
        logging.getLogger().setLevel(logging_level)
        logging.info("Initializing wordle solver...")
        logging.info(f"There are {len(word_list)} word in the word list!")
        self.word_list = word_list
        self.word_length = WordLength(word_list)

    def simulate(self, *, true_word : str, max_steps : int, first_guess=None):
        assert len(true_word) == self.word_length
        curr_word_list = self.word_list
        if first_guess is None:
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list)
            (top_rank_word, score) = ranked_candidates[0]
        else:
            top_rank_word = first_guess
            score = -1
        logging.info(f"Top word is <{top_rank_word}> with a score {score}.")
        word_status = GetWordStatus(guess_word=top_rank_word, true_word=true_word)
        logging.info(f"Word status: ({true_word} - {top_rank_word}):")
        logging.info(StatusToString(word_status))
        if AllYes(word_status):
            return 1
        curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                       guess_word=top_rank_word, guess_word_status=word_status)
        for step in range(1, max_steps):
            logging.info(f"\n.......Step {step}......")
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list)
            (top_rank_word, score) = ranked_candidates[0]
            logging.info(f"Top word is <{top_rank_word}> with a score {score}.")
            word_status = GetWordStatus(guess_word=top_rank_word, true_word=true_word)
            logging.info(f"Word status: ({true_word} - {top_rank_word}): " + StatusToString(word_status))
            if AllYes(word_status):
                return step + 1
            curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                           guess_word=top_rank_word, guess_word_status=word_status)
        return -1

    def test_performance(self):
        result = {}
        for i, word in enumerate(self.word_list):
            print(f"Process {i} / {len(self.word_list)}")
            steps = self.simulate(true_word=word, max_steps=100, first_guess='raise')
            if steps in result:
                result[steps] += 1.0
            else:
                result[steps] = 1.0
        print(result)


    def interactive_solve(self, true_word=None, max_steps=10):
        curr_word_list = self.word_list
        for step in range(max_steps):
            logging.info(f"\n.......Step {step}......")
            guess_word = input("Enter Word: ")
            assert len(guess_word) == self.word_length
            if true_word is None:
                status_str = input("Enter status (Yes = 0, Exist = 1, No = 2): ")
                assert len(status_str) == self.word_length
                word_status = DigitStringToWordStatus(status_str)
            else:
                word_status = GetWordStatus(guess_word=guess_word, true_word=true_word)
            if AllYes(word_status):
                print("Success!")
                return step+1
            curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                           guess_word=guess_word, guess_word_status=word_status)
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list)
            (top_rank_word, score) = ranked_candidates[0]
            print(f"Top word is <{top_rank_word}> with a score {score}.")
