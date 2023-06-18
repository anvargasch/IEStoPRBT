# -*- coding: utf-8 -*-
"""ReadIES.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19T7LJlMHFvND6eXWEEZXecYhupdGe4V_
"""

import re                         # function to open plain files
import os                         # function to save EXR files
os.environ["OPENCV_IO_ENABLE_OPENEXR"]="1"
import imageio                    # function to open EXR files
import cv2                        # computer vision library (open images, etc.)
import numpy as np                # functions for arrays

"""#Base functions"""

#File type information: http://docs.autodesk.com/ACD/2011/ESP/filesAUG/WS73099cc142f48755f058a10f71c104f3-3b1a.htm

def load_IES(filename):
    with open(filename, 'r') as file:
        content = file.read()
    match = re.search(r'TILT=', content)
    if not match:
        raise ValueError('Formato de archivo IES no válido')
    else:
      file=content.splitlines()
      index=0
      #print(len(file))
      for x in range(len(file)):
        #print(file[x])
        match = re.search(r'TILT=', file[x])
        if match:
          index=x
          x=len(file)
    return file, index # devuelve una lista con el archivo fotométrico e indice en donde inicia TILT

def header(IES, index):
    val=IES[index+1].split()
    Lumen=val[1]
    fact=val[2]
    Num_vert_angle=int(val[3])
    Num_hori_angle=int(val[4])
    unid=int(val[6]) # 1 para pies o 2 para metros
    return (Lumen,fact,Num_vert_angle,Num_hori_angle,unid) # devuelve parametros de la fotometría

def angles (file,index,num):
    aux=file[index].split()
    angle=np.array(aux)
    N_index = index +1
    N_angles=len(aux)
    if N_angles<num:
      for x in range(len(file)-index):
        aux=file[N_index].split()
        angle2=np.array(aux)
        N_angles=N_angles+len(aux)
        N_index = N_index +1
        angle = np.concatenate((angle, angle2), axis=0)
        if N_angles>=num:
          break
    angle = np.asarray(angle, dtype=float)
    return angle, N_index

def intensity_matrix (file,index,num_ver,num_hor):
    N_index = index
    mat=file[N_index].split()
    for x in range(len(file)-index-1):
      #print(N_index)
      N_index = N_index +1
      aux=file[N_index].split();
      mat=np.concatenate((mat, aux), axis=0)
    mat=np.resize(mat,(num_hor,num_ver))
    #print("Angulos Horizontales :",angle )
    mat = np.asarray(mat, dtype=float)
    return mat.T


def adjust_vert_angle(mat,angle_vertical,Num_vert_angle,Num_hori_angle):
  first_angle=angle_vertical[0]
  last_angle=angle_vertical[Num_vert_angle-1]

  if first_angle==0 and last_angle==90:
    aux=np.linspace(90,180,Num_vert_angle)
    aux=np.delete(aux, 0)
    angle_vertical=np.concatenate((angle_vertical, aux), axis=0)
    aux2=np.zeros((Num_vert_angle-1,Num_hori_angle))
    mat=np.concatenate((mat, aux2), axis=0)
  if first_angle==90 and last_angle==180:
    aux=np.linspace(0,90,Num_vert_angle)
    aux=np.delete(aux, 0)
    angle_vertical=np.concatenate((aux,angle_vertical), axis=0)
    aux2=np.zeros((Num_vert_angle-1,Num_hori_angle))
    mat=np.concatenate((aux2,mat), axis=0)
  return mat


def adjust_hor_angle(mat,angle_horizontal,Num_hori_angle):
  first_angle=angle_horizontal[0]
  if first_angle==0 and Num_hori_angle==1:
    angle_horizontal=np.linspace(0,90,6)
    Num_hori_angle=angle_horizontal.shape[0]
    aux=np.copy(mat)
    for x in range(Num_hori_angle-1):
      mat=np.concatenate((mat, aux), axis=1)
  last_angle=angle_horizontal[Num_hori_angle-1]
  if first_angle==0 and last_angle==90:
    aux1=np.linspace(90,180,Num_hori_angle)
    aux1=np.delete(aux1, 0)
    angle_horizontal=np.concatenate((angle_horizontal, aux1), axis=0)
    aux2=mat[:,::-1] ### Mirror matrix
    aux2=np.delete(aux2, 0, axis=1)
    mat=np.concatenate((mat, aux2), axis=1)
    Num_hori_angle=angle_horizontal.shape[0]
    last_angle=angle_horizontal[Num_hori_angle-1]
  if first_angle==0 and last_angle==180:
    aux1=np.linspace(180,360,Num_hori_angle)
    aux1=np.delete(aux1, 0)
    angle_horizontal=np.concatenate((angle_horizontal, aux1), axis=0)
    aux2=mat[:,::-1]
    aux2=np.delete(aux2, 0, axis=1)
    mat=np.concatenate((mat, aux2), axis=1)
    Num_hori_angle=angle_horizontal.shape[0]
    last_angle=angle_horizontal[Num_hori_angle-1]
  return mat

def PBRT_image (mat):
  resized = cv2.resize(mat, (720,360), interpolation = cv2.INTER_LINEAR)
  IES=np.rot90(resized, 2)
  img_normalized = cv2.normalize(IES, None, 0, 1.0, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
  return img_normalized

"""#General functions"""

#IES_header ----
def IES_header(filename):
  IES, index = load_IES(filename)
  if index!=0:
    Lumen,fact,Num_vert_angle,Num_hori_angle,unid = header(IES, index)
  return Lumen,fact,Num_vert_angle,Num_hori_angle,unid


#IES_Intensity_matrix ----

def IES_Intensity_matrix (filename):
  IES, index = load_IES(filename)
  if index!=0:
    Lumen, fact,Num_vert_angle,Num_hori_angle,unid = header(IES, index)
    if Num_vert_angle!=0:
      angle_vertical, index = angles(IES, index+3,Num_vert_angle)
      if Num_hori_angle!=0:
        angle_horizontal, index = angles(IES, index,Num_hori_angle)
        mat=intensity_matrix (IES,index,Num_vert_angle,Num_hori_angle)
  return mat

#IES2PBRT ----

def IES2PBRT (filename):
  IES, index = load_IES(filename)
  if index!=0:
    Lumen, fact,Num_vert_angle,Num_hori_angle,unid = header(IES, index)
    if Num_vert_angle!=0:
      angle_vertical, index = angles(IES, index+3,Num_vert_angle)
      if Num_hori_angle!=0:
        angle_horizontal, index = angles(IES, index,Num_hori_angle)
        mat=intensity_matrix (IES,index,Num_vert_angle,Num_hori_angle)
  mat=adjust_vert_angle(mat,angle_vertical,Num_vert_angle,Num_hori_angle)
  mat=adjust_hor_angle(mat,angle_horizontal,Num_hori_angle)
  img=PBRT_image(mat)
  return img

#PBRT save as EXR ----

def save_EXR(img_normalized, ruta):
  IMG_EXR=np.zeros((img_normalized.shape[0], img_normalized.shape[1],3))
  IMG_EXR[:,:,0]=img_normalized
  IMG_EXR[:,:,1]=img_normalized
  IMG_EXR[:,:,2]=img_normalized
  IMG_EXR = IMG_EXR.astype("float32")
  cv2.imwrite(ruta, IMG_EXR)
  return
