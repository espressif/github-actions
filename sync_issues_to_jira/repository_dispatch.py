#!/usr/bin/env python3

""" 
Method handles repository_dispatch event
"""
def handle_repository_dispatch(event):
    print('Removing all assignees from issue')
    print(f'{event = }')
