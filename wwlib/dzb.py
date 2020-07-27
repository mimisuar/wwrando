
from io import BytesIO

from fs_helpers import *

class DZB:
  def __init__(self):
    self.data = BytesIO()
    
    self.num_vertices = 0
    self.vertex_list_offset = None
    
    self.num_faces = 0
    self.face_list_offset = None
    
    self.num_octree_indexes = 0
    self.octree_index_list_offset = None
    self.num_octree_nodes = 0
    self.octree_node_list_offset = None
    
    self.num_groups = 0
    self.group_list_offset = None
    
    self.num_properties = 0
    self.property_list_offset = None
    
    self.unknown_1 = 0
    
    self.vertices = []
    self.faces = []
    self.groups = []
    self.properties = []
  
  def read(self, data):
    self.data = data
    
    self.num_vertices = read_u32(data, 0x00)
    self.vertex_list_offset = read_u32(data, 0x04)
    
    self.num_faces = read_u32(data, 0x08)
    self.face_list_offset = read_u32(data, 0x0C)
    
    self.num_octree_indexes = read_u32(data, 0x10)
    self.octree_index_list_offset = read_u32(data, 0x14)
    self.num_octree_nodes = read_u32(data, 0x18)
    self.octree_node_list_offset = read_u32(data, 0x1C)
    
    self.num_groups = read_u32(data, 0x20)
    self.group_list_offset = read_u32(data, 0x24)
    
    self.num_properties = read_u32(data, 0x28)
    self.property_list_offset = read_u32(data, 0x2C)
    
    self.unknown_1 = read_u32(data, 0x30)
    
    self.vertices = []
    offset = self.vertex_list_offset
    for vertex_index in range(0, self.num_vertices):
      vertex = Vertex(data)
      vertex.read(offset)
      self.vertices.append(vertex)
      offset += Vertex.DATA_SIZE
    
    self.faces = []
    offset = self.face_list_offset
    for face_index in range(0, self.num_faces):
      face = Face(data)
      face.read(offset)
      self.faces.append(face)
      offset += Face.DATA_SIZE
    
    # TODO: read octrees
    
    self.groups = []
    offset = self.group_list_offset
    for group_index in range(0, self.num_groups):
      group = Group(data)
      group.read(offset)
      self.groups.append(group)
      offset += Group.DATA_SIZE
    
    self.properties = []
    offset = self.property_list_offset
    for property_index in range(0, self.num_groups):
      property = Property(data)
      property.read(offset)
      self.properties.append(property)
      offset += Property.DATA_SIZE
    
    # Populate each face's extra attributes.
    for face in self.faces:
      face.vertices.append(self.vertices[face.vertex_1_index])
      face.vertices.append(self.vertices[face.vertex_2_index])
      face.vertices.append(self.vertices[face.vertex_3_index])
      face.property = self.properties[face.property_index]
      face.group = self.groups[face.group_index]
  
  def save_changes(self):
    self.data.truncate(0)
    data = self.data
    
    self.vertex_list_offset = 0x34
    self.data.seek(self.vertex_list_offset)
    offset = self.vertex_list_offset
    for vertex in self.vertices:
      vertex.offset = offset
      vertex.save_changes()
      offset += Vertex.DATA_SIZE
      
    self.face_list_offset = self.data.tell()
    offset = self.face_list_offset
    for face in self.faces:
      face.offset = offset
      face.vertex_1_index = self.vertices.index(face.vertices[0])
      face.vertex_2_index = self.vertices.index(face.vertices[1])
      face.vertex_3_index = self.vertices.index(face.vertices[2])
      face.property_index = self.properties.index(face.property)
      face.group_index    = self.groups.index(face.group)
      
      face.save_changes()
      offset += Face.DATA_SIZE
    
    # TODO: trees
    
    align_data_to_nearest(data, 4)
    self.property_list_offset = self.data.tell()
    offset = self.property_list_offset
    for property in self.properties:
      property.offset = offset
      property.save_changes()
      offset += Property.DATA_SIZE
    
    # TODO: blocks
    
    align_data_to_nearest(data, 4)
    self.group_list_offset = self.data.tell()
    offset = self.group_list_offset
    for group in self.groups:
      group.offset = offset
      group.save_changes()
      offset += Group.DATA_SIZE
    
    self.num_vertices = len(self.vertices)
    write_u32(data, 0x00, self.num_vertices)
    write_u32(data, 0x04, self.vertex_list_offset)
    
    self.num_faces = len(self.faces)
    write_u32(data, 0x08, self.num_faces)
    write_u32(data, 0x0C, self.face_list_offset)
    
    # TODO
    #write_u32(data, 0x10, self.num_octree_indexes)
    #write_u32(data, 0x14, self.octree_index_list_offset)
    #write_u32(data, 0x18, self.num_octree_nodes)
    #write_u32(data, 0x1C, self.octree_node_list_offset)
    
    self.num_groups = len(self.groups)
    write_u32(data, 0x20, self.num_groups)
    write_u32(data, 0x24, self.group_list_offset)
    
    self.num_properties = len(self.properties)
    write_u32(data, 0x28, self.num_properties)
    write_u32(data, 0x2C, self.property_list_offset)
    
    write_u32(data, 0x30, self.unknown_1)
  
  def add_face(self, vertex_positions, property, group):
    assert len(vertex_positions) == 3
    
    face = Face(self.data)
    self.faces.append(face)
    face.property = property
    face.group = group
    
    for x, y, z in vertex_positions:
      vertex = next((
        v for v in self.vertices
        if v.x_pos == x and v.y_pos == y and v.z_pos == z
      ), None)
      
      if vertex is None:
        vertex = Vertex(self.data)
        self.vertices.append(vertex)
        vertex.x_pos = x
        vertex.y_pos = y
        vertex.z_pos = z
      
      face.vertices.append(vertex)

class Vertex:
  DATA_SIZE = 0xC
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
  
  def read(self, offset):
    self.offset = offset
    
    self.x_pos = read_float(self.dzb_data, self.offset+0)
    self.y_pos = read_float(self.dzb_data, self.offset+4)
    self.z_pos = read_float(self.dzb_data, self.offset+8)
  
  def save_changes(self):
    write_float(self.dzb_data, self.offset+0, self.x_pos)
    write_float(self.dzb_data, self.offset+4, self.y_pos)
    write_float(self.dzb_data, self.offset+8, self.z_pos)

class Face:
  DATA_SIZE = 0xA
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.vertices = []
    self.property = None
    self.group = None
  
  def read(self, offset):
    self.offset = offset
    
    self.vertex_1_index = read_u16(self.dzb_data, self.offset+0)
    self.vertex_2_index = read_u16(self.dzb_data, self.offset+2)
    self.vertex_3_index = read_u16(self.dzb_data, self.offset+4)
    self.property_index = read_u16(self.dzb_data, self.offset+6)
    self.group_index    = read_u16(self.dzb_data, self.offset+8)
    
    # These will be populated by the DZB initialization function.
    self.vertices = []
    self.property = None
    self.group = None
  
  def save_changes(self):
    write_u16(self.dzb_data, self.offset+0, self.vertex_1_index)
    write_u16(self.dzb_data, self.offset+2, self.vertex_2_index)
    write_u16(self.dzb_data, self.offset+4, self.vertex_3_index)
    write_u16(self.dzb_data, self.offset+6, self.property_index)
    write_u16(self.dzb_data, self.offset+8, self.group_index)

class Octree:
  pass

class Group:
  DATA_SIZE = 0x34
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
  
  def read(self, offset):
    self.offset = offset
    
    self.name_offset = read_u32(self.dzb_data, self.offset+0x00)
    self.name = read_str_until_null_character(self.dzb_data, self.name_offset)
    
    self.x_scale = read_float(self.dzb_data, self.offset+0x04)
    self.y_scale = read_float(self.dzb_data, self.offset+0x08)
    self.z_scale = read_float(self.dzb_data, self.offset+0x0C)
    
    self.x_rot = read_u16(self.dzb_data, self.offset+0x10)
    self.y_rot = read_u16(self.dzb_data, self.offset+0x12)
    self.z_rot = read_u16(self.dzb_data, self.offset+0x14)
    
    self.unknown_1 = read_u16(self.dzb_data, self.offset+0x16) # Usually 0xFFFF, but sometimes 0xDCDC.
    
    self.x_translation = read_float(self.dzb_data, self.offset+0x18)
    self.y_translation = read_float(self.dzb_data, self.offset+0x1C)
    self.z_translation = read_float(self.dzb_data, self.offset+0x20)
    
    self.parent_group_index       = read_s16(self.dzb_data, self.offset+0x24)
    self.next_sibling_group_index = read_s16(self.dzb_data, self.offset+0x26)
    self.first_child_group_index  = read_s16(self.dzb_data, self.offset+0x28)
    
    self.room_index             = read_s16(self.dzb_data, self.offset+0x2A)
    self.unknown_2              = read_u16(self.dzb_data, self.offset+0x2C)
    self.octree_root_node_index = read_u16(self.dzb_data, self.offset+0x2E)
    
    group_info = read_u32(self.dzb_data, self.offset+0x30)
    self.rtbl_index = (group_info & 0x000000FF) >> 0
    self.is_water   = (group_info & 0x00000100) != 0
    self.is_lava    = (group_info & 0x00000200) != 0
    self.unused_1   = (group_info & 0x00000400) != 0
    self.sound_id   = (group_info & 0x0007F800) >> 11
    self.unused_2   = (group_info & 0xFFF80000) >> 19
  
  def save_changes(self):
    # TODO
    
    write_s16(self.dzb_data, self.offset+0x2A, self.room_index)
    
    group_info = 0
    group_info |= (self.rtbl_index << 0)  & 0x000000FF
    group_info |= (self.is_water   << 8)  & 0x00000100
    group_info |= (self.is_lava    << 9)  & 0x00000200
    group_info |= (self.unused_1   << 10) & 0x00000400
    group_info |= (self.sound_id   << 11) & 0x0007F800
    group_info |= (self.unused_2   << 19) & 0xFFF80000
    write_u32(self.dzb_data, self.offset+0x30, group_info)

class Property:
  DATA_SIZE = 0x10
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
  
  def read(self, offset):
    self.offset = offset
    
    bitfield_1 = read_u32(self.dzb_data, self.offset+0x00)
    self.cam_id     = (bitfield_1 & 0x000000FF) >> 0
    self.sound_id   = (bitfield_1 & 0x00001F00) >> 8
    self.exit_index = (bitfield_1 & 0x0007E000) >> 13
    self.poly_color = (bitfield_1 & 0x07F80000) >> 19
    self.unknown_1  = (bitfield_1 & 0xF8000000) >> 27
    
    bitfield_2 = read_u32(self.dzb_data, self.offset+0x04)
    self.link_no        = (bitfield_2 & 0x000000FF) >> 0
    self.wall_type      = (bitfield_2 & 0x00000F00) >> 8
    self.special_type   = (bitfield_2 & 0x0000F000) >> 12
    self.attribute_type = (bitfield_2 & 0x001F0000) >> 16
    self.ground_type    = (bitfield_2 & 0x03E00000) >> 21
    self.unknown_2      = (bitfield_2 & 0xFC000000) >> 26
    
    bitfield_3 = read_u32(self.dzb_data, self.offset+0x08)
    self.cam_move_bg        = (bitfield_3 & 0x000000FF) >> 0
    self.room_cam_id        = (bitfield_3 & 0x0000FF00) >> 8
    self.room_path_id       = (bitfield_3 & 0x00FF0000) >> 16
    self.room_path_point_no = (bitfield_3 & 0xFF000000) >> 24
    
    self.camera_behavior = read_u32(self.dzb_data, self.offset+0x0C)
  
  def save_changes(self):
    # TODO
    pass
