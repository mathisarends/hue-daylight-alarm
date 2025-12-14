import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  FlatList,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface AlarmModalProps {
  visible: boolean;
  onClose: () => void;
  onSave: (alarm: AlarmConfig) => void;
}

export interface AlarmConfig {
  time: string;
  recurring: string[];
  duration: number;
  lightScene: string;
  lightStartBrightness: number;
  lightEndBrightness: number;
  soundProfile: string;
  enabled: boolean;
}

const WEEKDAYS = [
  { label: 'M', value: 'monday' },
  { label: 'T', value: 'tuesday' },
  { label: 'W', value: 'wednesday' },
  { label: 'T', value: 'thursday' },
  { label: 'F', value: 'friday' },
  { label: 'S', value: 'saturday' },
  { label: 'S', value: 'sunday' },
];

const SOUND_PROFILES = [
  { id: 'gentle-waves', name: 'Gentle Waves', icon: 'water-outline' },
  { id: 'forest-birds', name: 'Forest Birds', icon: 'leaf-outline' },
  { id: 'morning-breeze', name: 'Morning Breeze', icon: 'cloudy-outline' },
  { id: 'soft-piano', name: 'Soft Piano', icon: 'musical-notes-outline' },
  { id: 'zen-bells', name: 'Zen Bells', icon: 'notifications-outline' },
];

const LIGHT_SCENES = [
  {
    id: 'sunrise',
    name: 'Follow a sunrise',
    description: 'Perfect sunrise with an energy boost.',
    colors: ['#89CFF0', '#FFB366'],
  },
  {
    id: 'warm-white',
    name: 'Warm white',
    description: 'Gentle warm light gradually increases.',
    colors: ['#FFF5E1', '#FFD700'],
  },
  {
    id: 'energize',
    name: 'Energize',
    description: 'Bright cool light to feel alert.',
    colors: ['#E0F7FF', '#4DD0E1'],
  },
  {
    id: 'golden-hour',
    name: 'Golden hour',
    description: 'Beautiful golden morning tones.',
    colors: ['#FFE5B4', '#FF8C00'],
  },
];

export const AlarmModal: React.FC<AlarmModalProps> = ({ visible, onClose, onSave }) => {
  const [hours, setHours] = useState(7);
  const [minutes, setMinutes] = useState(0);
  const [isPM, setIsPM] = useState(false);
  const [recurring, setRecurring] = useState<string[]>(['monday', 'tuesday', 'wednesday', 'thursday', 'friday']);
  const [duration, setDuration] = useState(30);
  const [lightScene, setLightScene] = useState('sunrise');
  const [lightStartBrightness, setLightStartBrightness] = useState(1);
  const [lightEndBrightness, setLightEndBrightness] = useState(100);
  const [soundProfile, setSoundProfile] = useState('gentle-waves');
  const [enabled, setEnabled] = useState(true);
  const [showLightScenes, setShowLightScenes] = useState(false);
  const [showSoundProfiles, setShowSoundProfiles] = useState(false);

  const hoursList = Array.from({ length: 12 }, (_, i) => i + 1);
  const minutesList = Array.from({ length: 60 }, (_, i) => i);

  const toggleWeekday = (day: string) => {
    setRecurring(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const handleSave = () => {
    const displayTime = `${hours}:${minutes.toString().padStart(2, '0')} ${isPM ? 'PM' : 'AM'}`;
    onSave({
      time: displayTime,
      recurring,
      duration,
      lightScene,
      lightStartBrightness,
      lightEndBrightness,
      soundProfile,
      enabled,
    });
    onClose();
  };

  const calculateStartTime = () => {
    let totalMinutes = hours * 60 + minutes;
    if (isPM && hours !== 12) totalMinutes += 12 * 60;
    if (!isPM && hours === 12) totalMinutes -= 12 * 60;

    const startMinutes = totalMinutes - duration;
    const startHours = Math.floor(startMinutes / 60) % 24;
    const startMins = startMinutes % 60;
    const startPeriod = startHours >= 12 ? 'PM' : 'AM';
    const displayHours = startHours % 12 || 12;

    return `${displayHours}:${startMins.toString().padStart(2, '0')} ${startPeriod}`;
  };

  const renderTimeItem = (item: number, isSelected: boolean, isHour: boolean) => (
    <TouchableOpacity
      style={[styles.timeItem, isSelected && styles.timeItemSelected]}
      onPress={() => isHour ? setHours(item) : setMinutes(item)}
    >
      <Text style={[styles.timeItemText, isSelected && styles.timeItemTextSelected]}>
        {isHour ? item : item.toString().padStart(2, '0')}
      </Text>
    </TouchableOpacity>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          {/* Header */}
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Rise and shine</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={28} color="#000" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* Title */}
            <Text style={styles.sectionMainTitle}>Wake me up at</Text>

            {/* Interactive Time Picker */}
            <View style={styles.section}>
              <View style={styles.interactiveTimePicker}>
                <View style={styles.timePickerRow}>
                  <View style={styles.timeColumn}>
                    <FlatList
                      data={hoursList}
                      renderItem={({ item }) => renderTimeItem(item, item === hours, true)}
                      keyExtractor={(item) => `hour-${item}`}
                      showsVerticalScrollIndicator={false}
                      contentContainerStyle={styles.timeListContent}
                      snapToInterval={50}
                      decelerationRate="fast"
                    />
                  </View>
                  <Text style={styles.timeSeparator}>:</Text>
                  <View style={styles.timeColumn}>
                    <FlatList
                      data={minutesList}
                      renderItem={({ item }) => renderTimeItem(item, item === minutes, false)}
                      keyExtractor={(item) => `minute-${item}`}
                      showsVerticalScrollIndicator={false}
                      contentContainerStyle={styles.timeListContent}
                      snapToInterval={50}
                      decelerationRate="fast"
                    />
                  </View>
                  <View style={styles.periodColumn}>
                    <TouchableOpacity
                      style={[styles.periodButton, !isPM && styles.periodButtonActive]}
                      onPress={() => setIsPM(false)}
                    >
                      <Text style={[styles.periodText, !isPM && styles.periodTextActive]}>AM</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.periodButton, isPM && styles.periodButtonActive]}
                      onPress={() => setIsPM(true)}
                    >
                      <Text style={[styles.periodText, isPM && styles.periodTextActive]}>PM</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            </View>

            {/* Duration */}
            <View style={styles.section}>
              <View style={styles.durationCard}>
                <View style={styles.iconWithText}>
                  <Ionicons name="timer-outline" size={24} color="#666" />
                  <View>
                    <Text style={styles.sectionTitle}>Over {duration} min</Text>
                    <Text style={styles.subtext}>Lights rise from {calculateStartTime()}</Text>
                  </View>
                </View>
                <TouchableOpacity>
                  <Ionicons name="chevron-down" size={20} color="#666" />
                </TouchableOpacity>
              </View>
            </View>

            {/* Light Scenes */}
            <View style={styles.section}>
              <TouchableOpacity
                style={styles.menuCard}
                onPress={() => setShowLightScenes(!showLightScenes)}
              >
                <View style={styles.menuCardLeft}>
                  <View style={styles.menuIconContainer}>
                    <View style={styles.sunriseGradientSmall}>
                      <View style={styles.gradientTopSmall} />
                      <View style={styles.gradientBottomSmall} />
                    </View>
                  </View>
                  <View>
                    <Text style={styles.menuCardTitle}>Set the lights</Text>
                    <Text style={styles.menuCardSubtitle}>
                      {LIGHT_SCENES.find(s => s.id === lightScene)?.name}
                    </Text>
                  </View>
                </View>
                <Ionicons
                  name={showLightScenes ? "chevron-up" : "chevron-down"}
                  size={20}
                  color="#666"
                />
              </TouchableOpacity>

              {showLightScenes && (
                <View style={styles.subMenu}>
                  {LIGHT_SCENES.map((scene) => (
                    <TouchableOpacity
                      key={scene.id}
                      style={[
                        styles.sceneCard,
                        lightScene === scene.id && styles.sceneCardActive
                      ]}
                      onPress={() => {
                        setLightScene(scene.id);
                        setShowLightScenes(false);
                      }}
                    >
                      <View style={styles.sceneGradient}>
                        <View style={[styles.sceneGradientTop, { backgroundColor: scene.colors[0] }]} />
                        <View style={[styles.sceneGradientBottom, { backgroundColor: scene.colors[1] }]} />
                      </View>
                      <View style={styles.sceneContent}>
                        <Text style={styles.sceneTitle}>{scene.name}</Text>
                        <Text style={styles.sceneDescription}>{scene.description}</Text>
                      </View>
                      {lightScene === scene.id && (
                        <View style={styles.sceneCheckmark}>
                          <Ionicons name="checkmark-circle" size={24} color="#000" />
                        </View>
                      )}
                    </TouchableOpacity>
                  ))}

                  {/* Brightness Settings */}
                  <View style={styles.brightnessContainer}>
                    <View style={styles.brightnessRow}>
                      <Text style={styles.brightnessLabel}>Start brightness</Text>
                      <View style={styles.brightnessValueContainer}>
                        <Text style={styles.brightnessValue}>{lightStartBrightness}%</Text>
                        <View style={[styles.brightnessIndicator, { opacity: lightStartBrightness / 100 }]} />
                      </View>
                    </View>
                    <View style={styles.brightnessRow}>
                      <Text style={styles.brightnessLabel}>End brightness</Text>
                      <View style={styles.brightnessValueContainer}>
                        <Text style={styles.brightnessValue}>{lightEndBrightness}%</Text>
                        <View style={[styles.brightnessIndicator, { opacity: lightEndBrightness / 100, backgroundColor: '#FFD700' }]} />
                      </View>
                    </View>
                  </View>
                </View>
              )}
            </View>

            {/* Sound Profile */}
            <View style={styles.section}>
              <TouchableOpacity
                style={styles.menuCard}
                onPress={() => setShowSoundProfiles(!showSoundProfiles)}
              >
                <View style={styles.menuCardLeft}>
                  <View style={styles.menuIconContainer}>
                    <Ionicons
                      name={SOUND_PROFILES.find(s => s.id === soundProfile)?.icon as any}
                      size={24}
                      color="#666"
                    />
                  </View>
                  <View>
                    <Text style={styles.menuCardTitle}>Wake-up sound</Text>
                    <Text style={styles.menuCardSubtitle}>
                      {SOUND_PROFILES.find(s => s.id === soundProfile)?.name}
                    </Text>
                  </View>
                </View>
                <Ionicons
                  name={showSoundProfiles ? "chevron-up" : "chevron-down"}
                  size={20}
                  color="#666"
                />
              </TouchableOpacity>

              {showSoundProfiles && (
                <View style={styles.subMenu}>
                  {SOUND_PROFILES.map(profile => (
                    <TouchableOpacity
                      key={profile.id}
                      style={[
                        styles.soundProfileItem,
                        soundProfile === profile.id && styles.soundProfileItemActive
                      ]}
                      onPress={() => {
                        setSoundProfile(profile.id);
                        setShowSoundProfiles(false);
                      }}
                    >
                      <View style={styles.soundProfileContent}>
                        <Ionicons name={profile.icon as any} size={24} color="#666" />
                        <Text style={styles.soundProfileText}>{profile.name}</Text>
                      </View>
                      {soundProfile === profile.id && (
                        <Ionicons name="checkmark-circle" size={24} color="#000" />
                      )}
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* Recurring Days */}
            <View style={styles.section}>
              <Text style={styles.sectionMainTitle}>Recurring</Text>
              <View style={styles.weekdaysContainer}>
                {WEEKDAYS.map((day) => (
                  <TouchableOpacity
                    key={day.value}
                    style={[
                      styles.weekdayButton,
                      recurring.includes(day.value) && styles.weekdayButtonActive
                    ]}
                    onPress={() => toggleWeekday(day.value)}
                  >
                    <Text
                      style={[
                        styles.weekdayText,
                        recurring.includes(day.value) && styles.weekdayTextActive
                      ]}
                    >
                      {day.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={{ height: 20 }} />
          </ScrollView>

          {/* Save Button */}
          <View style={styles.footer}>
            <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
              <Text style={styles.saveButtonText}>Save Alarm</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    height: '95%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    position: 'relative',
  },
  closeButton: {
    position: 'absolute',
    right: 20,
    top: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  scrollContent: {
    padding: 20,
  },
  section: {
    marginBottom: 28,
  },
  sectionMainTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  subtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  iconWithText: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  // Interactive Time Picker
  interactiveTimePicker: {
    backgroundColor: '#f8f8f8',
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
  },
  timePickerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  timeColumn: {
    height: 150,
    width: 60,
  },
  timeListContent: {
    paddingVertical: 50,
  },
  timeItem: {
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timeItemSelected: {
    backgroundColor: 'transparent',
  },
  timeItemText: {
    fontSize: 24,
    color: '#ccc',
  },
  timeItemTextSelected: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#000',
  },
  timeSeparator: {
    fontSize: 32,
    fontWeight: 'bold',
    marginHorizontal: 4,
  },
  periodColumn: {
    gap: 8,
    marginLeft: 8,
  },
  periodButton: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 16,
    backgroundColor: '#fff',
    minWidth: 50,
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: '#000',
  },
  periodText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  periodTextActive: {
    color: '#fff',
  },
  // Duration Card
  durationCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 16,
    borderRadius: 12,
  },
  // Menu Cards
  menuCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8f8f8',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
  },
  menuCardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  menuIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  menuCardTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  menuCardSubtitle: {
    fontSize: 12,
    color: '#666',
  },
  sunriseGradientSmall: {
    width: '100%',
    height: '100%',
    flexDirection: 'column',
  },
  gradientTopSmall: {
    flex: 1,
    backgroundColor: '#89CFF0',
  },
  gradientBottomSmall: {
    flex: 1,
    backgroundColor: '#FFB366',
  },
  subMenu: {
    marginTop: 8,
    gap: 12,
  },
  // Light Scenes
  sceneCard: {
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  sceneCardActive: {
    borderColor: '#000',
  },
  sceneGradient: {
    height: 100,
    flexDirection: 'column',
  },
  sceneGradientTop: {
    flex: 1,
  },
  sceneGradientBottom: {
    flex: 1,
  },
  sceneContent: {
    padding: 16,
    backgroundColor: '#f8f8f8',
  },
  sceneTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  sceneDescription: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
  },
  sceneCheckmark: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  brightnessContainer: {
    backgroundColor: '#f8f8f8',
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  brightnessRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  brightnessLabel: {
    fontSize: 14,
    color: '#333',
  },
  brightnessValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brightnessValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  brightnessIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#FFD700',
  },
  // Weekdays
  weekdaysContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  weekdayButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#f5f5f5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  weekdayButtonActive: {
    backgroundColor: '#000',
  },
  weekdayText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
  },
  weekdayTextActive: {
    color: '#fff',
  },
  // Sound Profile
  soundProfileItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f8f8f8',
    borderRadius: 12,
    marginBottom: 8,
  },
  soundProfileItemActive: {
    backgroundColor: '#e8e8e8',
  },
  soundProfileContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  soundProfileText: {
    fontSize: 16,
    fontWeight: '500',
  },
  // Footer
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  saveButton: {
    backgroundColor: '#000',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default AlarmModal;
