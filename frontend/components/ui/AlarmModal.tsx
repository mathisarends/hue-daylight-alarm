import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Switch,
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

export const AlarmModal: React.FC<AlarmModalProps> = ({ visible, onClose, onSave }) => {
  const [time, setTime] = useState('7:00');
  const [isPM, setIsPM] = useState(false);
  const [recurring, setRecurring] = useState<string[]>(['monday', 'tuesday', 'wednesday', 'thursday', 'friday']);
  const [duration, setDuration] = useState(30);
  const [lightStartBrightness, setLightStartBrightness] = useState(1);
  const [lightEndBrightness, setLightEndBrightness] = useState(100);
  const [soundProfile, setSoundProfile] = useState('gentle-waves');
  const [enabled, setEnabled] = useState(true);

  const toggleWeekday = (day: string) => {
    setRecurring(prev =>
      prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
    );
  };

  const handleSave = () => {
    const displayTime = `${time} ${isPM ? 'PM' : 'AM'}`;
    onSave({
      time: displayTime,
      recurring,
      duration,
      lightScene: 'sunrise',
      lightStartBrightness,
      lightEndBrightness,
      soundProfile,
      enabled,
    });
    onClose();
  };

  const calculateStartTime = () => {
    const [hours, minutes] = time.split(':').map(Number);
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
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color="#000" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>When do you want to wake up?</Text>
          </View>

          <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* Description */}
            <Text style={styles.description}>
              We'll slowly increase the lights so you wake up gently over a {duration}-minute period.
            </Text>

            {/* Time Picker */}
            <View style={styles.section}>
              <View style={styles.timePickerContainer}>
                <View style={styles.timeDisplay}>
                  <Ionicons name="time-outline" size={24} color="#666" />
                  <Text style={styles.timeText}>{time} {isPM ? 'PM' : 'AM'}</Text>
                </View>
                <View style={styles.timePeriodToggle}>
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
              <Text style={styles.subtext}>Lights rise from {calculateStartTime()}</Text>
            </View>

            {/* Recurring Days */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Recurring on</Text>
              <View style={styles.weekdaysContainer}>
                {WEEKDAYS.map(day => (
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

            {/* Duration */}
            <View style={styles.section}>
              <View style={styles.sectionHeader}>
                <View style={styles.iconWithText}>
                  <Ionicons name="timer-outline" size={20} color="#666" />
                  <Text style={styles.sectionTitle}>Over {duration} min</Text>
                </View>
                <TouchableOpacity>
                  <Ionicons name="chevron-down" size={20} color="#666" />
                </TouchableOpacity>
              </View>
              <Text style={styles.subtext}>Lights rise from {calculateStartTime()}</Text>
            </View>

            {/* Light Scene */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Set the lights</Text>
              <View style={styles.lightSceneCard}>
                <View style={styles.sunriseGradient}>
                  <View style={styles.gradientTop} />
                  <View style={styles.gradientBottom} />
                </View>
                <View style={styles.lightSceneContent}>
                  <Text style={styles.lightSceneTitle}>Follow a sunrise</Text>
                  <Text style={styles.lightSceneSubtitle}>
                    Set the perfect sunrise for you and start the day with an energy boost.
                  </Text>
                </View>
              </View>

              {/* Brightness Settings */}
              <View style={styles.brightnessContainer}>
                <View style={styles.brightnessRow}>
                  <Text style={styles.brightnessLabel}>Lights start at</Text>
                  <View style={styles.brightnessValueContainer}>
                    <Text style={styles.brightnessValue}>{lightStartBrightness}%</Text>
                    <View style={[styles.brightnessIndicator, { backgroundColor: '#FFB366' }]} />
                  </View>
                </View>
                <View style={styles.brightnessRow}>
                  <Text style={styles.brightnessLabel}>Lights end at</Text>
                  <View style={styles.brightnessValueContainer}>
                    <Text style={styles.brightnessValue}>{lightEndBrightness}%</Text>
                    <View style={[styles.brightnessIndicator, { backgroundColor: '#FF8533' }]} />
                  </View>
                </View>
              </View>
            </View>

            {/* Sound Profile */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Wake-up sound</Text>
              {SOUND_PROFILES.map(profile => (
                <TouchableOpacity
                  key={profile.id}
                  style={[
                    styles.soundProfileItem,
                    soundProfile === profile.id && styles.soundProfileItemActive
                  ]}
                  onPress={() => setSoundProfile(profile.id)}
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

            {/* Enable Switch */}
            <View style={styles.section}>
              <View style={styles.enableRow}>
                <View style={styles.enableContent}>
                  <Ionicons name="alarm-outline" size={24} color="#000" />
                  <View>
                    <Text style={styles.enableTitle}>{time} {isPM ? 'PM' : 'AM'}</Text>
                    <Text style={styles.enableSubtitle}>
                      {recurring.length === 7 ? 'Daily' : recurring.length > 0 ? 'Weekdays' : 'No repeat'}
                    </Text>
                  </View>
                </View>
                <Switch
                  value={enabled}
                  onValueChange={setEnabled}
                  trackColor={{ false: '#ddd', true: '#000' }}
                  thumbColor="#fff"
                />
              </View>
            </View>
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
    maxHeight: '90%',
  },
  modalHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  closeButton: {
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  scrollContent: {
    padding: 20,
  },
  description: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 24,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  iconWithText: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  subtext: {
    fontSize: 12,
    color: '#666',
  },
  timePickerContainer: {
    backgroundColor: '#f5f5f5',
    padding: 20,
    borderRadius: 12,
    marginBottom: 8,
  },
  timeDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  timeText: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  timePeriodToggle: {
    flexDirection: 'row',
    gap: 8,
  },
  periodButton: {
    paddingVertical: 8,
    paddingHorizontal: 20,
    borderRadius: 20,
    backgroundColor: '#fff',
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
  lightSceneCard: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 16,
  },
  sunriseGradient: {
    height: 80,
    position: 'relative',
  },
  gradientTop: {
    flex: 1,
    backgroundColor: '#89CFF0',
  },
  gradientBottom: {
    flex: 1,
    backgroundColor: '#FFB366',
  },
  lightSceneContent: {
    padding: 16,
    backgroundColor: '#f5f5f5',
  },
  lightSceneTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  lightSceneSubtitle: {
    fontSize: 12,
    color: '#666',
    lineHeight: 18,
  },
  brightnessContainer: {
    backgroundColor: '#f5f5f5',
    padding: 16,
    borderRadius: 12,
    gap: 16,
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
  },
  soundProfileItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f5f5f5',
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
  enableRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
  },
  enableContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  enableTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  enableSubtitle: {
    fontSize: 12,
    color: '#666',
  },
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
