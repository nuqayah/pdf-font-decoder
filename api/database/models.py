from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base


class SVGFile(Base):
    __tablename__ = 'svg_files'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    content = Column(Text)
    upload_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    fonts = relationship('FontFile', back_populates='svg_file')


class FontFile(Base):
    __tablename__ = 'font_files'

    id = Column(Integer, primary_key=True, index=True)
    svg_file_id = Column(Integer, ForeignKey('svg_files.id'))
    font_name = Column(String, index=True)
    filename = Column(String)
    upload_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    svg_file = relationship('SVGFile', back_populates='fonts')
    glyphs = relationship('Glyph', back_populates='font_file')


class Glyph(Base):
    __tablename__ = 'glyphs'

    id = Column(Integer, primary_key=True, index=True)
    font_file_id = Column(Integer, ForeignKey('font_files.id'))
    codepoint = Column(String, index=True)
    preview_image = Column(Text)
    mapping = Column(String, default='')
    is_mapped = Column(Boolean, default=False)

    font_file = relationship('FontFile', back_populates='glyphs')
