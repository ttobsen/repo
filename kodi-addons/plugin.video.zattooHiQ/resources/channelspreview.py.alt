# coding=utf-8
#
#	Copyright (C) 2015 Daniel Griner (griner.ch@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#



REMOTE_DBG = False
# append pydev remote debugger
if REMOTE_DBG:
	# Make pydev debugger works for auto reload.
	# Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
	try:
		import pysrc.pydevd as pydevd  # with the addon script.module.pydevd, only use `import pydevd`
	# stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
		#pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True, suspend=False)
		pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)
	except ImportError:
		sys.stderr.write("Error: You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
		sys.exit(1)
#





import xbmc, xbmcgui, xbmcaddon, time, threading
from resources.zattooDB import ZattooDB

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_SELECT_ITEM = 7
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10

KEY_NAV_BACK = 92
KEY_HOME = 159

ACTION_MOUSE_DOUBLE_CLICK = 103
ACTION_MOUSE_DRAG = 106
ACTION_MOUSE_END = 109
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_LONG_CLICK = 108
ACTION_MOUSE_MIDDLE_CLICK = 102
ACTION_MOUSE_MOVE = 107
ACTION_MOUSE_RIGHT_CLICK = 101
ACTION_MOUSE_START = 100
ACTION_MOUSE_WHEEL_DOWN = 105
ACTION_MOUSE_WHEEL_UP = 104
ACTION_BUILT_IN_FUNCTION = 122

__addon__ = xbmcaddon.Addon()
__addonId__=__addon__.getAddonInfo('id')

class ChannelsPreview(xbmcgui.Window):
	#print('FAV:'+str(fav))
	#favourites=favourites

	def __init__(self):
		#super(ChannelsPreview, self).__init__()

		self.channels = []
		self.programms = []
		self.controls = []
		self.selected = 0
		self.highlightImage = ''
		self.startChannel = 0
		self.refreshTimerRunning=False
		self.updateNr=0
		self.setProperty('ret', '')
		#self.createPreview(fav)


	'''
	def onInit(self):
		i = 10  # why isn't this called!?
#		 self.createPreview()

	def onClick(self, controlId):
		print('CLICKED')
		i = 20  # why isn't this called!?

	def onFocus(self):
		print('HASFOCUS')
	'''

	def onAction(self, action):
		action = action.getId()
		#print('previewAction'+str(action))
		if action in [ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU]:
			self.close()
			#print('SELF CLOSE')
			self.refreshTimerRunning=False
			#xbmc.executebuiltin("PreviousMenu")
		#elif action in [ACTION_BUILT_IN_FUNCTION]:
			#self.close()
		elif action == ACTION_MOVE_LEFT:
			self.moveHighlight(-1)
		elif action == ACTION_MOVE_RIGHT:
			self.moveHighlight(1)
		elif action == ACTION_MOVE_UP:
			self.moveHighlight(-5)
		elif action == ACTION_MOVE_DOWN:
			self.moveHighlight(5)
		elif action == ACTION_SELECT_ITEM:
			self.refreshTimerRunning=False
			#self.close()
			url = "plugin://"+__addonId__+"/?mode=watch_c&id=" + self.controls[self.selected]['channel']
			xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
			#xbmc.executebuiltin("Action(FullScreen)")

        '''
		elif action == ACTION_MOUSE_MOVE:
			xbmcgui.Dialog().notification('mouse', 'move', '', 000, False)
		elif action == ACTION_MOUSE_LEFT_CLICK:
			xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(Klick,line1, time,))
		elif action == ACTION_MOUSE_DRAG:
			xbmcgui.Dialog().notification('mouse', 'drag', '', 000, False)
        '''

	def createPreview(self, fav):
		imgW = 256
		imgH = 150

		# collect all controls and add them in one call to save time
		allControls = []

		# create preview images first so they are behind highlight image
		images = []
		for y in range(0, 4):
			for x in range(0, 5):
				image = xbmcgui.ControlImage(x * imgW, y * 180 + 1, imgW - 2, imgH, '')
				allControls.append(image)
				images.append(image)

		self.highlightImage = xbmcgui.ControlImage(0, 0, imgW, 178, '')
		allControls.append(self.highlightImage)
		self.highLabel=''

		#add a scroll label for highlighted item
		self.scrollLabel = xbmcgui.ControlFadeLabel(0,0, 240, 30, 'font13', '0xFFFFFFFF')
		allControls.append(self.scrollLabel)

		#preloadImage is buffer for image update
		self.preloadImage = xbmcgui.ControlImage(0, -200, 256, 150, '')
		allControls.append(self.preloadImage)

		for y in range(0, 4):
			for x in range(0, 5):
				logo = xbmcgui.ControlImage((x * imgW) + 5, y * 180 + 100, 84, 48, '')
				label = xbmcgui.ControlLabel(x * imgW + 6, y * 180 + imgH - 1, 250, 30, 'font13')
				channelNr = xbmcgui.ControlLabel(x * imgW + 200, y * 180 + 5, 50, 20, 'font13', alignment=1)

				allControls.append(logo)
				allControls.append(label)
				allControls.append(channelNr)

				self.controls.append({
					'image':images[y * 5 + x],
					'logo':logo,
					'label':label,
					'channelNr':channelNr,
					'visible':True
				})

		self.addControls(allControls)

		db = ZattooDB()
		self.channels = db.getChannelList(fav)
		currentChannel = db.get_playing()['channel']
		#highlight current channel
		start=self.channels[currentChannel]['nr']
		self.showChannels(int(start/20)*20)
		self.moveHighlight(start%20)

		self.highlightImage.setImage(xbmcaddon.Addon().getAddonInfo('path') + '/resources/channel-highlight.png')

		self.refreshTimerRunning=True
		self.refreshImageNr=0
		#self.refreshPreviewImages()
		#threading.Timer(10, self.refreshPreviewImages).start()

	def showChannels(self, start):
		self.startChannel = start
		channels = self.channels
		programms = ZattooDB().getPrograms(channels)

		for nr in range(0, 20):
			current = start + nr
			control = self.controls[nr]

			if current > (len(channels) - 2): #-2: skip channel['index']
				control['image'].setVisible(False)
				control['logo'].setVisible(False)
				control['label'].setVisible(False)
				control['channelNr'].setVisible(False)
				control['visible'] = False
			else:
				currenChannel= channels[channels['index'][current]]
				title = ''
				for search in programms:
					if search['channel'] == currenChannel['id']:
						title = search ['title']
						#title = search ['title'] +'    '+ search['start_date'].strftime('%H:%M') + '-' + search['end_date'].strftime('%H:%M')
						break

				control['logo'].setImage(currenChannel['logo'])
				control['label'].setLabel(title)
				control['channelNr'].setLabel(str(current+1))
				control['channel'] = currenChannel['id']
				if control['visible'] == False:
					control['image'].setVisible(True)
					control['logo'].setVisible(True)
					control['label'].setVisible(True)
					control['channelNr'].setVisible(True)
					control['visible'] = True

		#show images
		now = int(time.time())
		for control in self.controls:
			if control['visible']:
				src = 'http://thumb.zattic.com/' + control['channel'] + '/500x288.jpg?r=' + str(now)
				control['image'].setImage(src, False)
				self.preloadImageSrc=src




	def refreshPreviewImages(self):
		now = int(time.time())

		control=self.controls[self.refreshImageNr]
		if control['visible']:
			src = 'http://thumb.zattic.com/' + control['channel'] + '/500x288.jpg?r=' + str(now)
			self.controls[self.refreshImageNr-1]['image'].setImage(self.preloadImageSrc, False)
			self.preloadImage.setImage(src, False)
			self.preloadImageSrc=src

		self.refreshImageNr+=1
		if self.refreshImageNr>19:self.refreshImageNr=0

		#if self.refreshTimerRunning:
		#	threading.Timer(2, self.refreshPreviewImages).start()

	def moveHighlight(self, step):
		#reset label
		if self.highLabel: self.controls[self.selected]['label'].setLabel(self.highLabel)
		selected = self.selected + step
		#print('selected'+str(self.selected))

		if selected > 19:
			self.showChannels(self.startChannel + 20)
			self.selected = selected - 20
		elif selected < 0:
			if (self.startChannel > 19):
				self.showChannels(self.startChannel - 20)
				self.selected = selected + 20
			else: return
		else:
			if self.controls[selected]['visible']: self.selected = selected
			else:return

		selected = self.selected
		x = (selected % 5) * 256 - 1
		y = int(selected / 5) * 180 + 1

		'''
		#moving highlight
		pos=self.highlightImage.getPosition()
		stepX=(x-pos[0])/10
		stepY=(y-pos[1])/10

		for nr in range(1, 10):
			self.highlightImage.setPosition(pos[0]+(stepX*nr), pos[1]+(stepY*nr))
			xbmc.sleep(10)
		'''

		self.highlightImage.setPosition(x, y)

		title=self.controls[self.selected]['label'].getLabel()
		self.controls[self.selected]['label'].setLabel('')
		self.highLabel=title
		self.scrollLabel.reset()
		self.scrollLabel.setPosition(x+7,y+148)
		self.scrollLabel.addLabel(title)

