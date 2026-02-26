(つ▀¯▀ )つ GAUCHO INSIGHTS ⊂(▀¯▀⊂ )
IndexError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/gaucho-insights/main_app.py", line 193, in <module>
    main()
    ~~~~^^
File "/mount/src/gaucho-insights/main_app.py", line 104, in main
    rmp = prof_history.sort_values(['year_val', 'q_weight'], ascending=False).iloc[0]
          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/indexing.py", line 1192, in __getitem__
    return self._getitem_axis(maybe_callable, axis=axis)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/indexing.py", line 1753, in _getitem_axis
    self._validate_integer(key, axis)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/indexing.py", line 1686, in _validate_integer
    raise IndexError("single positional indexer is out-of-bounds")
