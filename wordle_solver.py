from enum import Enum
from typing import List
import copy
import logging
import math
from time import time

from multiprocessing import Pool
import functools


def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func


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

def StatusToDigitString(guess_word_status : List[LetterStatus]):
    digit_str = ''
    for status in guess_word_status:
        if status == LetterStatus.Yes:
            digit_str += '0'
        elif status == LetterStatus.No:
            digit_str += '2'
        elif status == LetterStatus.Exist:
            digit_str += '1'
        else:
            assert False
    return digit_str


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

# TODO: Speed up the loop...
def CalculateWordScoreHelper(*, word_list : List[str], guess_word : str, get_word_status_func, depth):
    status_frequency_dict = {}
    for word in word_list:
        status = get_word_status_func(guess_word=guess_word, true_word=word)
        status_str = StatusToDigitString(status)
        if status_str in status_frequency_dict:
            status_frequency_dict[status_str] += 1.0
        else:
            status_frequency_dict[status_str] = 1.0

    expected_entropy = 0
    p_sum = 0
    for (k, v) in status_frequency_dict.items():
        p = v / len(word_list)
        p_sum += p
        if depth == 1:
            info = -math.log2(p)
        else:
            new_word_list = PruneWordList(curr_word_list=word_list, guess_word=guess_word,
                                          guess_word_status=DigitStringToWordStatus(k),
                                          get_word_status_func=get_word_status_func)
            ranked_candidates = GenerateRankedCandidates(word_list=new_word_list,
                                                         get_word_status_func=get_word_status_func,
                                                         depth=depth-1)
            info = ranked_candidates[0][1]

        expected_entropy += p*info
    return expected_entropy

def CalculateWordScore(*, word_list : List[str], guess_word : str, get_word_status_func, depth):
    return CalculateWordScoreHelper(word_list=word_list, guess_word=guess_word,
                                    get_word_status_func=get_word_status_func,
                                    depth=depth)

# TODO: Two nested loop here could be processed in parallel...
def GenerateRankedCandidates(word_list : List[str], get_word_status_func, depth=1):
    ranked_candidates = []
    for i, word in enumerate(word_list):
        score = CalculateWordScore(word_list=word_list, guess_word=word, get_word_status_func=get_word_status_func,
                                   depth=depth)
        ranked_candidates.append((word, score))
        if i % 100 == 0:
            logging.debug(f"Processing {i}/{len(word_list)} word...")
    ranked_candidates.sort(reverse=True, key=lambda elem:elem[1])
    return ranked_candidates


def AllYes(guess_word_status):
    return all([status == LetterStatus.Yes for status in guess_word_status])


def PruneWordList(*, curr_word_list, guess_word, guess_word_status, get_word_status_func):
    new_word_list = []
    for word in curr_word_list:
        word_status = get_word_status_func(guess_word=guess_word, true_word=word)
        if StatusToString(word_status) == StatusToString(guess_word_status):
            new_word_list.append(word)
    assert len(new_word_list)!=0, "Sorry, our word list doesn't contain the True Word..."
    return new_word_list


class Simulater(object):
    def __init__(self, wordle_solver, first_guess):
        self.wordle_solver = wordle_solver
        self.first_guess = first_guess
    def __call__(self, true_word):
        return self.wordle_solver.simulate(true_word=true_word, max_steps=100, first_guess=self.first_guess)


@timer_func
class GetWordStatusWithCache(object):
    def __init__(self, word_list):
        self.word_list = word_list
        self.status_cache = {}
        for guess_word in word_list:
            if guess_word in self.status_cache:
                guess_word_status_dict = self.status_cache[guess_word]
            else:
                self.status_cache[guess_word] = {}
                guess_word_status_dict = self.status_cache[guess_word]
            for true_word in word_list:
                    if not (true_word in guess_word_status_dict):
                        guess_word_status_dict[true_word] = GetWordStatus(guess_word=guess_word, true_word=true_word)
    def __call__(self, guess_word, true_word):
        return self.status_cache[guess_word][true_word]


class WordleSolver():
    def __init__(self, word_list : List[str], logging_level = logging.INFO, max_num_process=8, build_cache=True):
        logging.basicConfig()
        logging.getLogger().setLevel(logging_level)
        logging.info("Initializing wordle solver...")
        logging.info(f"There are {len(word_list)} word in the word list!")
        self.word_list = word_list
        self.word_length = WordLength(word_list)
        self.max_num_process = max_num_process
        if build_cache:
            print("Building cache....")
            self.get_word_status_func = GetWordStatusWithCache(word_list)
        else:
            self.get_word_status_func = GetWordStatus

    def simulate(self, *, true_word : str, max_steps : int, first_guess=None):
        assert len(true_word) == self.word_length
        curr_word_list = self.word_list
        if first_guess is None:
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list,
                                                         get_word_status_func=self.get_word_status_func)
            (top_rank_word, score) = ranked_candidates[0]
        else:
            top_rank_word = first_guess
            score = -1
        logging.info(f"Top word is <{top_rank_word}> with a score {score}.")
        word_status = self.get_word_status_func(guess_word=top_rank_word, true_word=true_word)
        logging.info(f"Word status: ({true_word} - {top_rank_word}):")
        logging.info(StatusToString(word_status))
        if AllYes(word_status):
            return 1
        curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                       guess_word=top_rank_word, guess_word_status=word_status,
                                       get_word_status_func=self.get_word_status_func)
        for step in range(1, max_steps):
            logging.info(f"\n.......Step {step}......")
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list,
                                                         get_word_status_func=self.get_word_status_func)
            (top_rank_word, score) = ranked_candidates[0]
            logging.info(f"Top word is <{top_rank_word}> with a score {score}.")
            word_status = self.get_word_status_func(guess_word=top_rank_word, true_word=true_word)
            logging.info(f"Word status: ({true_word} - {top_rank_word}): " + StatusToString(word_status))
            if AllYes(word_status):
                return step + 1
            curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                           guess_word=top_rank_word, guess_word_status=word_status,
                                           get_word_status_func=self.get_word_status_func)
        return -1


    @timer_func
    def test_performance(self, first_guess='raise'):
        stats = {}
        with Pool(self.max_num_process) as p:
            results = p.map(Simulater(self, first_guess), self.word_list)
        for steps in results:
            if steps in stats:
                stats[steps] += 1.0
            else:
                stats[steps] = 1.0
        average = 0.0
        for i in sorted(stats) :
            print ((i, stats[i]), end =" ")
            average += i * stats[i] / float(len(self.word_list));
        print(f"\n average performance: {average}")


    def test_performance_loop(self, first_guess="raise"):
        stats = {}
        for i, word in enumerate(self.word_list):
            # print(f"Process {i} / {len(self.word_list)}")
            steps = self.simulate(true_word=word, max_steps=100, first_guess='raise')
            if steps in stats:
                stats[steps] += 1.0
            else:
                stats[steps] = 1.0
        average = 0.0
        for i in sorted(stats) :
            print ((i, stats[i]), end =" ")
            average += i * stats[i] / float(len(self.word_list));
        print(f"\n average performance: {average}")

    def interactive_solve(self, true_word=None, max_steps=10):
        ranked_candidates = GenerateRankedCandidates(word_list=self.word_list,
                                                     get_word_status_func=self.get_word_status_func)
        (top_rank_word, score) = ranked_candidates[0]
        print(f"Top word is <{top_rank_word}> with a score {score}.")


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
                word_status = self.get_word_status_func(guess_word=guess_word, true_word=true_word)
            if AllYes(word_status):
                print("Success!")
                return step+1
            curr_word_list = PruneWordList(curr_word_list=curr_word_list,
                                           guess_word=guess_word,
                                           guess_word_status=word_status,
                                           get_word_status_func=self.get_word_status_func)
            ranked_candidates = GenerateRankedCandidates(word_list=curr_word_list,
                                                         get_word_status_func=self.get_word_status_func)
            (top_rank_word, score) = ranked_candidates[0]
            print(f"Top word is <{top_rank_word}> with a score {score}.")
