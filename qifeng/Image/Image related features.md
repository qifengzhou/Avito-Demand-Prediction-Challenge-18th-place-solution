1. **Labels and probabilities extraction from pretrained model**

Using pretrained models, predict the labels. The assumption is that when the model can recognise well, so so human. Using VGG16, XceptionV3 and Inception models pretrained on Imagenet.

__Run pretrained in kernel__ (https://www.kaggle.com/gaborfodor/keras-pretrained-models/kernels)

Three models: Wesam Elshamy [Ad Image Recognition and Quality Scoring](https://www.kaggle.com/wesamelshamy/ad-image-recognition-and-quality-scoring)

- *forked from above, combined with #2 manual.* 
    [Peter HurfordImage Feature Engineering](https://www.kaggle.com/peterhurford/image-feature-engineering)

RAW features after conv layers:
- DUO [Extract avito image features via keras VGG16](https://www.kaggle.com/classtag/extract-avito-image-features-via-keras-vgg16) # 25088 dim features, suggested to reduce with PCA?
- Bruno G. do Amaral [VGG16 Train features](https://www.kaggle.com/bguberfain/vgg16-train-features/code)

2. **Manual image features extraction**

Dull, whiteness, colorness, pixels, number of colors, size. That are the things will influece human perception and maybe decision making. 

sban [Avito - Ideas for Image Features and Image Quality](https://www.kaggle.com/shivamb/avito-ideas-for-image-features-and-image-quality)
