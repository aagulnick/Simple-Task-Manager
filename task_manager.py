# Future to-do:
# GUI: always show output of display() and re-render when another command is executed
# Drag-and-drop in GUI's table, when sorting is by priority, should change moved item's priority to the line you dragged it to (1-indexed)

import datetime
from tabulate import tabulate
memory_path = "C:\python\organization\memory.txt"
# some abbreviations below, so you can type sort(p) instead of sort("priority"), etc.
p = "priority"
d = "due date"

def load_data(file_path):
    """Given a text file, load data into the task_list and current_sorting variables.
    Return a tuple (task_list, current_sorting).
    WARNING: evaluates the second line of the txt file. Do not run if you do not trust the file!"""
    with open(memory_path, 'r+') as f:
        task_list = []
        current_sorting = "due date"
        for i, line in enumerate(f):
            if i == 0:
                current_sorting = str(line.strip("\n"))
            if i == 1:
                task_list = [Task(task[0], due_date=task[1], priority=task[2]) for task in eval(line)]
    return task_list, current_sorting


def save_data(file_path):
    """Write task_list and current_sorting to the specified file.
    The first line is the current_sorting.
    The second line is a list whose entries are 3-tuples (name, due_date, priority)."""
    result = f"{current_sorting}\n{[(task.name, task.due_date, task.priority) for task in task_list]}"
    with open(file_path, 'w+') as f:
        f.write(result)


class Task:
    def __init__(self, name, due_date=None, priority=None):
        self.name = name
        self.due_date = due_date
        self.priority = priority
    
    def get_name(self):
        return self.name
    def rename(self, new_name):
        self.name = new_name
    
    def get_due_date(self):
        return self.due_date
    def set_due_date(self, new_date):
        self.due_date = new_date

    def get_priority(self):
        return self.priority
    def set_priority(self, new_priority):
        self.priority = new_priority

    def __str__(self):
        return f"{self.name} | Due {self.due_date} | Priority {self.priority}"


def add(task_name, task_due_date=None, task_priority=None):
    """Create a new task and add it to the task_list. If priority is specified, inserts at that priority
    above whatever currently has that priority.
    NOTE: mutates task_list"""
    if task_due_date:
        split_date = task_due_date.split('/')
        due_date = datetime.date(int(split_date[2]), int(split_date[0]), int(split_date[1]))
    else:
        due_date = None
    
    if task_priority is not None:
        for old_task in task_list:
            if old_task.priority is not None and old_task.priority >= task_priority:
                old_task.priority += 1

    task = Task(task_name, due_date, task_priority)
    task_list.append(task)
    save_data(memory_path)

def remove(name):
    """Removes the first task with the specified name."""
    task = None
    for item in task_list:
        if item.get_name() == name:
            task = item
            break
    if task:
        for item in task_list:
            if task.priority is not None and item.priority is not None and item.priority > task.priority:
                item.priority -= 1  # removing a task means shifting down everything above it
        task_list.remove(task)
    save_data(memory_path)

def sort(sort_type):
    """Set current_sorting.
    NOTE: mutates current_sorting"""
    # both sorting procedures give tuples (T/F, x)
    # since False < True, these are sorted by True first, then sorted by value of appropriate field
    global current_sorting
    if type(sort_type) is str and sort_type.lower() in ["due date", "priority"]:
        current_sorting = sort_type.lower()
    save_data(memory_path)

def display():
    """Sorts the task_list as necessary and then displays it."""
    global task_list
    global current_sorting
    if current_sorting.lower() == "due date":
        task_list = sorted(task_list, key=lambda x: (x.get_due_date() is None, x.get_due_date()))
    else:  # current_sorting.lower() == "priority"
        task_list = sorted(task_list, key=lambda x: (x.get_priority() is None, x.get_priority()))

    print(f"Displaying To-Do List with sorting by {current_sorting}\n")
    # print(tabulate([[task.name, task.due_date, task.priority] for task in task_list], headers=["Name", "Due Date", "Priority"]))
    return tabulate([[task.name, task.due_date, task.priority] for task in task_list], headers=["Name", "Due Date", "Priority"])


def update_priority(name, new_priority):
    """Find the first task with the given name and update its priority to new_priority.
    Any intermediate priorities are adjusted."""
    task = None
    for t in task_list:
        if t.name == name:
            task = t
            break
    if task:  # if we found a task of the right name
        old_priority = task.priority
        for other in task_list:
            if old_priority is not None and other.priority is not None and other.priority < old_priority and other.priority >= new_priority:
                other.priority += 1
            if old_priority is not None and other.priority is not None and other.priority > old_priority and other.priority <= new_priority:
                other.priority -= 1
        task.priority = new_priority
    save_data(memory_path)

def remove_priority(name):
    """Makes the priority field of the given task None."""
    task = None
    for t in task_list:
        if t.name == name:
            task = t
            break
    if task:
        for t in task_list:
            if t.priority is not None and task.priority is not None and t.priority >= task.priority:
                t.priority -= 1
        task.priority = None
    save_data(memory_path)

def update_date(name, new_date):
    task = None
    for t in task_list:
        if t.name == name:
            task = t
            break
    if task:
        split_date = new_date.split('/')
        task.due_date = datetime.date(int(split_date[2]), int(split_date[0]), int(split_date[1]))
    save_data()

def remove_date(name):
    task = None
    for t in task_list:
        if t.name == name:
            task = t
            break
    if task:
        task.due_date = None
    save_data()

def help():
    """Print the controls."""
    print(f"Commands: display(), sort('due date' OR 'priority'),\nadd(task), remove(task),\nupdate_priority(task_name:str, new_priority:int), remove_priority(task_name:str)\nwhere a Task has fields name:str, due_date:str 'MM/DD/YYYY', priority:int")

task_list, current_sorting = load_data(memory_path)