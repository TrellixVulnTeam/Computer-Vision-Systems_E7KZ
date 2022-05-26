import json
import os
from collections import namedtuple

import torch
import torch.utils.data as data
from PIL import Image
import numpy as np


class Cityscapes(data.Dataset):
    """Cityscapes <http://www.cityscapes-dataset.com/> Dataset.
    
    **Parameters:**
        - **root** (string): Root directory of dataset where directory 'leftImg8bit' and 'gtFine' or 'gtCoarse' are located.
        - **split** (string, optional): The image split to use, 'train', 'test' or 'val' if mode="gtFine" otherwise 'train', 'train_extra' or 'val'
        - **mode** (string, optional): The quality mode to use, 'gtFine' or 'gtCoarse' or 'color'. Can also be a list to output a tuple with all specified target types.
        - **transform** (callable, optional): A function/transform that takes in a PIL image and returns a transformed version. E.g, ``transforms.RandomCrop``
        - **target_transform** (callable, optional): A function/transform that takes in the target and transforms it.
    """

    # Based on https://github.com/mcordts/cityscapesScripts
    CityscapesClass = namedtuple('CityscapesClass', ['name', 'id', 'train_id', 'category', 'category_id',
                                                     'has_instances', 'ignore_in_eval', 'color'])
    classes = [
        CityscapesClass('none',          0, 0, '0', 0, False, True, (0, 0, 0)),
        CityscapesClass('Buildings',          1, 1, '1', 1, True, False, (70, 70, 70)),
        CityscapesClass('Fences',          2, 2, '2', 2, True, False, (190, 153, 153)),
        CityscapesClass('Other',          3, 3, '3', 3, True, False, (72, 0, 90)),
        CityscapesClass('Pedestrians',          4, 4, '4', 4, True, False, (220, 20, 60)),
        CityscapesClass('Poles',          5, 5, '5', 5, True, False, (153, 153, 153)),
        CityscapesClass('RoadLines',          6, 6, '5', 5, True, False, (157, 234, 50)),
        CityscapesClass('Roads',          7, 7, '5', 5, True, False, (128, 64, 128)),
        CityscapesClass('Sidewalks',          8, 8, '5', 5, True, False, (244, 35, 232)),
        CityscapesClass('Vegetation',          9, 9, '5', 5, True, False, (107, 142, 35)),
        CityscapesClass('Vehicles',          10, 10, '5', 5, True, False, (0, 0, 255)),
        CityscapesClass('Walls',          11, 11, '5', 5, True, False, (102, 102, 156)),
        CityscapesClass('TrafficSigns',          12, 12, '5', 5, True, False, (220, 220, 0)),
    ]

    train_id_to_color = [c.color for c in classes if (c.train_id != -1 and c.train_id != 255)]
    # train_id_to_color.append([0, 0, 0])
    train_id_to_color = np.array(train_id_to_color)
    id_to_train_id = np.array([c.train_id for c in classes])

    #train_id_to_color = [(0, 0, 0), (128, 64, 128), (70, 70, 70), (153, 153, 153), (107, 142, 35),
    #                      (70, 130, 180), (220, 20, 60), (0, 0, 142)]
    #train_id_to_color = np.array(train_id_to_color)
    #id_to_train_id = np.array([c.category_id for c in classes], dtype='uint8') - 1

    def __init__(self, root, split='train', mode='fine', target_type='semantic', transform=None):
        self.root = os.path.expanduser(root)
        self.mode = 'masks'
        self.target_type = target_type
        self.images_dir = os.path.join(self.root,split, 'images')

        self.targets_dir = os.path.join(self.root,split, self.mode)
        self.transform = transform

        self.split = split
        self.images = []
        self.targets = []

        for city in os.listdir(self.images_dir):
            img_dir = os.path.join(self.images_dir, city)
            target_dir = os.path.join(self.targets_dir, city)[:-3]+'png'

            self.images.append(os.path.join(img_dir))

            self.targets.append(os.path.join(target_dir))

    @classmethod
    def encode_target(cls, target):

        target = np.array(target)[...,:3]
        for i,color in enumerate(cls.train_id_to_color.tolist()):

            target[target==color]=i
        target[target>13]=0

        return Image.fromarray(target[...,0])

    @classmethod
    def decode_target(cls, target):
        # target[target == 255] = 19
        target = target.astype('uint8') + 1

        return cls.train_id_to_color[target]

    def __getitem__(self, index):
        """
        Args:
            index (int): Index
        Returns:
            tuple: (image, target) where target is a tuple of all target types if target_type is a list with more
            than one item. Otherwise target is a json object if target_type="polygon", else the image segmentation.
        """
        image = Image.open(self.images[index]).convert('RGB')
        target = Image.open(self.targets[index])

        target = self.encode_target(target)
        if self.transform:
            #print(image.size,target.shape)
            image, target = self.transform(image, target)


        #print(target)


        return image, target

    def __len__(self):
        return len(self.images)

    def _load_json(self, path):
        with open(path, 'r') as file:
            data = json.load(file)
        return data

    def _get_target_suffix(self, mode, target_type):
        if target_type == 'instance':
            return '{}.png'.format(mode)
        elif target_type == 'semantic':
            return '{}_labelIds.png'.format(mode)
        elif target_type == 'color':
            return '{}_color.png'.format(mode)
        elif target_type == 'polygon':
            return '{}_polygons.json'.format(mode)
        elif target_type == 'depth':
            return '{}_disparity.png'.format(mode)