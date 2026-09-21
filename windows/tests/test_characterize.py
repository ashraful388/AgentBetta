from agentbetta.core.characterize import characterize
from agentbetta.core.models import Task

def test_characterizes_file_code_task():
    f=characterize(Task("Analyze this repository and debug the Python tests"))
    assert f.needs_files and f.needs_code and f.reasoning_level >= 1

def test_characterizes_calculation():
    assert characterize(Task("Calculate 17 * 23")).needs_calculation


def test_characterizes_browsing_task():
    f = characterize(Task("can you browse through my chrome browser?"))
    assert f.needs_network
    assert not f.needs_files


def test_url_does_not_imply_file_task():
    f = characterize(Task("open https://example.com and tell me the title"))
    assert f.needs_network
    assert not f.needs_files


def test_browser_words_need_boundaries():
    assert not characterize(Task("explain the opposite of a monochrome image")).needs_network


def test_complex_build_tasks_need_a_stronger_tier():
    assert characterize(Task("Build a production-ready React UI with a modular design")).reasoning_level >= 1
    # A long, detailed prompt is treated as complex too.
    assert characterize(Task("do this: " + "step " * 200)).reasoning_level >= 1


def test_characterizes_local_pc_access_question():
    f = characterize(Task("can you access my local pc?"))
    assert f.needs_files
    assert not characterize(Task("summarize the specification")).needs_files


def test_run_intent_enables_shell_and_process_tools():
    f = characterize(Task("now run it"))
    assert f.needs_shell and f.needs_process
    assert characterize(Task("execute the deploy script")).needs_shell


def test_run_word_needs_boundaries():
    assert not characterize(Task("prune the branches")).needs_shell
