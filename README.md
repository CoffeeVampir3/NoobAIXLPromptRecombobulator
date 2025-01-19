![Alt text](https://raw.githubusercontent.com/CoffeeVampir3/NoobAIXLPromptRecombobulator/2788e2c26a5dfec49ab01ec375323ae8e527629e/image.png)

### For NoobAI-XL Models
Like ![](https://huggingface.co/Laxhar/noobai-XL-Vpred-1.0)

This will reformat a list of tags into the recommended ordering based on their danbooru tag, highlight aliased tags, and warn you if something is not a tag. Gray tags (unknown) will likely decrease the quality of a prompt. Any artist names will automatically be tagged `artist:name` as recommended by the prompting format. 

Run via
```
python interface.py
```

### Prompting Notes:

The interface will load the tags stored in danbooru-date-underscore.csv. Only danbooru tags are used right now. Tags from ![BetaDoggo](https://github.com/BetaDoggo/danbooru-tag-list)
