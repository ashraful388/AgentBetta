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


def test_characterizes_local_pc_access_question():
    f = characterize(Task("can you access my local pc?"))
    assert f.needs_files
    assert not characterize(Task("summarize the specification")).needs_files
