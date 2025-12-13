import React from 'react';
import { TouchableOpacity, View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface RoomCardProps {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  backgroundColor: string;
  hasDevice?: boolean;
  onPress?: () => void;
}

export const RoomCard: React.FC<RoomCardProps> = ({
  title,
  icon,
  backgroundColor,
  hasDevice = false,
  onPress
}) => {
  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor }]}
      onPress={onPress}
    >
      <View style={styles.header}>
        <Ionicons name={icon} size={24} color="#000" />
        <Text style={styles.title}>{title}</Text>
      </View>
      {hasDevice && (
        <View style={styles.deviceIcon}>
          <Ionicons name="bulb-outline" size={20} color="#000" />
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 20,
    borderRadius: 20,
    marginBottom: 12,
    minHeight: 120,
    justifyContent: 'space-between',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  deviceIcon: {
    width: 36,
    height: 36,
    backgroundColor: '#fff',
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
