# -*- coding: utf-8 -*-
import os
from AutoUpload import AutoUpload

inputDir = '//romeo/Collect/AutoUpload'

if len(os.listdir(inputDir)) > 0:
	AutoUpload(inputDir)